# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import requests
import base64
import json
import time
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
from dateutil.parser import parse
from dash.dependencies import Input, Output, State
requests.packages.urllib3.disable_warnings()

import conf

def auth_tb(username, password):
    try:
       headers = {'charset':'utf-8','Content-Type':'application/json', 'Accept':'application/json', 'Authorization':'Bearer ' + conf.gw_token }
       url = conf.url + "/api/auth/login"
       data = "{\"username\":\"" + username + "\",\"password\":\"" + password + "\"}"
       post_resp = requests.post(url, data, headers=headers, verify=True)
       if post_resp.status_code == 200:
          return post_resp
       else:
          return
    except requests.exceptions.ConnectionError:
       return

def get_timeseries_data(device_id, key, startTs, endTs, interval, agg, limit, token):
    try:
       headers = {'charset':'utf-8','Content-Type':'application/json', 'Accept':'application/json', 'X-Authorization': 'Bearer ' + token, 'Authorization':'Bearer ' + conf.gw_token }
       url = conf.url + "/api/plugins/telemetry/DEVICE/" + device_id + \
             "/values/timeseries?keys=" + key + "&startTs=" + startTs + "&endTs=" + endTs + "&interval=" + interval + "&limit=" + limit + "&agg=" + agg
       get_resp = requests.get(url, headers=headers, verify=False)
       if get_resp.status_code == 200:
          return get_resp
       else:
          return
    except requests.exceptions.ConnectionError:
       return

def get_currentmillis(year, month, day, start):
    if (start == True):
       v = datetime(int(year), int(month), int(day), 0, 0, 0, 360700)
    else:
       v = datetime(int(year), int(month), int(day), 23, 59, 59, 360700)
    d = time.mktime(v.timetuple()) * 1000
    return "{0:13.0f}".format(d)

def update_plot(date, key, deviceid):
    res = auth_tb(conf.username, conf.password)
    if res != None:
       token = res.json()['token']
    year,month,day = date.split('-')
    start = str(get_currentmillis(year, month, day, True))
    stop = str(get_currentmillis(year, month, day, False))
    interval = str(86400000)
    agg = "NONE"
    limit = str(60000)

    value = []
    ts = []
    res = get_timeseries_data(deviceid, key, start, stop, interval, agg, limit, token)
    data = res.json()
    if res != None and data.has_key(key):
       params = data[key]
       for j in range(len(params)):
          value.append(float(params[j]['value'])/10)
          tsproc = datetime.fromtimestamp(int(params[j]['ts'])/1000).strftime('%Y-%m-%d %H:%M:%S')
          ts.append(tsproc)
       #print ts
       #print value

    if key == "rsrp":
       defination = "RSRP (dBm)"
       titled = "Time Series Plot for NB-IoT Reference Signal Received Power (RSRP)" 
    elif key == "snr":
       defination = "SNR (dB)"
       titled = "Time Series Plot for NB-IoT Signal to Noise Ratio (SNR)"
    else:
       defination = "RSRQ (dBm)"
       titled = "Time Series Plot for NB-IoT Reference Signal Received Quality (RSRQ)"

    trace = go.Scatter(x = ts, y = value,
                       name = defination,
                       line = dict(width = 2, color = 'rgb(0, 0, 204)'))
    layout = go.Layout(title = titled, hovermode = 'closest')
    fig = go.Figure(data = [trace], layout = layout)
    return fig

fig_init = update_plot("2019-01-01", "rsrp", "36a8d4b0-618c-11e8-ab9e-8f4bf9a263e5")

def serve_layout():
    return html.Main(
        [
            dcc.Dropdown(
                id='deviceid',
                options=[
                    {'label': 'ST1', 'value': ''},
                    {'label': 'ST2', 'value': ''},
                    {'label': 'ST3', 'value': ''},
                    {'label': 'ST4', 'value': ''},
                    {'label': 'ST5', 'value': ''},
                    {'label': 'ST6', 'value': ''},
                    {'label': 'ST7', 'value': ''},
                    {'label': 'ST8', 'value': ''},
                    {'label': 'ST9', 'value': ''},
                    {'label': 'ST10', 'value': ''},
                    {'label': 'STDemo', 'value': ''}
                ],
                value='36a8d4b0-618c-11e8-ab9e-8f4bf9a263e5'
            ),
            dcc.Dropdown(
                id='key',
                options=[
                    {'label': 'RSRP', 'value': 'rsrp'},
                    {'label': 'RSRQ', 'value': 'rsrq'},
                    {'label': 'SNR', 'value': 'snr'}
                ],
                value='rsrp'
            ),
            dcc.DatePickerSingle(
                id='datepicker',
            # layout settings
                first_day_of_week=1,
                display_format='YYYY-MM-DD',
                placeholder='Select Date',
            # date defaults
                date=datetime.now(),
            # date limits
                min_date_allowed=datetime(2018, 1, 1),
                # today
                max_date_allowed=datetime.now(),
                initial_visible_month=datetime(
                    datetime.now().year,
                    datetime.now().month,
                    1
                )
            ),
            html.Button(
                'Select Date',
                id='button'
            ),
            dcc.Graph(id='plot', figure=fig_init)
        ],
    )

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = serve_layout

@app.callback(Output('plot', 'figure'), [Input('button', 'n_clicks'), Input('datepicker', 'date'), Input('deviceid','value'), Input('key', 'value')])
def update_graph(clicks, selected_date, device, metric):
    if (clicks is not None) and (clicks > 0):
        fig = update_plot(selected_date, metric, device)
        return fig
    else:
        sdate = datetime.today().strftime('%Y-%m-%d')
        fig = update_plot(sdate, metric, device)
        return fig

if __name__ == '__main__':
    app.run_server(debug=True)
