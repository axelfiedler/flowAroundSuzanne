# -*- coding: utf-8 -*-
"""
Created on Sun Jan 27 15:48:00 2019

@author: fiedl
"""

import json
import dash
import os
import pandas as pd
import dash_core_components as dcc
import plotly.graph_objs as go
import dash_html_components as html
from dash.dependencies import Input, Output
from textwrap import dedent as d
import numpy as np

app = dash.Dash(__name__)

styles = {
    'pre': {
        'border': 'thin lightgrey solid'
    }
}

def loadResultFile(case,Re):
    residuals = pd.read_csv('data/residuals_'+case+'/Re_'+str(Re)+'.dat',
                header=1, sep='\t+', engine='python')

    Cd = pd.read_csv('data/C_D_'+case+'/Re_'+str(Re)+'.dat',
                header=8, sep='\t+', engine='python')

    Cd.columns = ['Time', 'Cm', 'Cd', 'Cl', 'Cl_f', 'Cl_r']

    residuals.columns = ['Time', 'Ux', 'Uy', 'Uz', 'p']

    return Cd, residuals

def updateResultDicts():
    cases = []
    for item in os.listdir('data'):
        cases.append(item.rpartition('_')[-1])
    cases = list(set(cases))
    for case in cases:
        forces_dict[case] = {}
        residuals_dict[case] = {}
        final_residuals[case] = {}
        final_Cd[case] = {}
        for item in os.listdir('data/residuals_'+case):
            Re = int(item.rpartition('_')[-1].rpartition('.')[0])
            forces, residuals = loadResultFile(case,Re)
            forces_dict[case][Re] = forces
            residuals_dict[case][Re] = residuals
            final_residuals[case][Re] = residuals.tail(1)
            final_Cd[case][Re] = forces['Cd'].tail(1).tolist()[0]

def getFinalCdTraces():
    data = []
    for forces_case in forces_dict:
        x_values = forces_dict[forces_case].keys()
        y_values = final_Cd[forces_case].values()
        x_values, y_values = zip(*sorted(zip(x_values, y_values)))
        trace = go.Scatter(
        x = x_values,
        y = y_values,
        mode = 'lines+markers',
        name = forces_case,
        )
        data.append(trace)
    return data


def getResidualTraces(case,Re):
    trace0 = go.Scatter(
        x = residuals_dict[case][Re]['Time'],
        y = residuals_dict[case][Re]['p'],
        mode = 'lines',
        name = 'p'
    )
    trace1 = go.Scatter(
        x = residuals_dict[case][Re]['Time'],
        y = residuals_dict[case][Re]['Ux'],
        mode = 'lines',
        name = 'Ux'
    )
    trace2 = go.Scatter(
        x = residuals_dict[case][Re]['Time'],
        y = residuals_dict[case][Re]['Uy'],
        mode = 'lines',
        name = 'Uy'
    )
    trace3 = go.Scatter(
        x = residuals_dict[case][Re]['Time'],
        y = residuals_dict[case][Re]['Uz'],
        mode = 'lines',
        name = 'Uz'
    )
    data = [trace0, trace1, trace2, trace3]
    return data

forces_dict = {}
residuals_dict = {}

final_residuals = {}
final_Cd = {}

updateResultDicts()

app.layout = html.Div([
    html.H1(children="Flow around Blender\'s Suzanne",className='headline'),
    html.Div(
    id="description",
    children="Shows the results of a simpleFoam calculation to estimate the drag coefficient of Blender\'s Suzanne. Click on a point in upper graph to update graphs below."),
    html.Div([
        dcc.Graph(
            id='overview',
            figure=go.Figure(
                data=getFinalCdTraces(),
                layout=dict(
                title='Final values of Cd of Suzanne vs. Reynolds number',
                hovermode='closest',
                xaxis={'title': 'Reynolds number'},
                yaxis={'title': 'Drag coefficient Cd'},
                clickmode= 'event+select')
            )
        )
    ],className='overview-container'),
    html.Div([
        dcc.Graph(
            id='iterations',
            figure=go.Figure(
                data=[
                    go.Scatter(
                    x = forces_dict['laminar'][100]['Time'],
                    y = forces_dict['laminar'][100]['Cd'],
                    mode = 'lines',
                )],
                layout=dict(
                title='Convergence of Cd for Re = 100 (laminar)',
                xaxis={'title': 'Iterations'},
                yaxis={'title': 'Drag coefficient Cd'},
                hovermode='closest')
            )
        )
    ],className='small-graphs-containers'),
    html.Div([
        dcc.Graph(
            id='residuals',
            figure=go.Figure(
                data= getResidualTraces('laminar',100),
                layout=dict(
                title='Residuals for Re = 100 (laminar)',
                xaxis={'title': 'Iterations'},
                yaxis={'title': 'Residuals', 'type': 'log'},
                hovermode='closest')
            )
        )
    ],className='small-graphs-containers'),
    html.Div([
        dcc.Graph(
            id='mesh',
            figure=go.Figure(
                layout=dict(
                title='Mesh study',
                xaxis={'title': 'No. of elements'},
                yaxis={'title': 'Drag coefficient Cd'},
                hovermode='closest')
            )
        )
    ],className='small-graphs-containers')

],className='center')

@app.callback(
    Output('iterations', 'figure'),
    [Input('overview', 'clickData')])
def update_figure(clickData):
    selected_Re = clickData['points'][0]['x']
    curve_number = clickData['points'][0]['curveNumber']
    trace_name = forces_dict.keys()[curve_number]
    return {
        'data': [go.Scatter(
            x=forces_dict[trace_name][selected_Re]['Time'],
            y=forces_dict[trace_name][selected_Re]['Cd'],
            mode='lines'
        )],
        'layout': go.Layout(
            title='Convergence of Cd for Re = '+str(selected_Re)+' ('+trace_name+')',
            xaxis={'title': 'Iterations'},
            yaxis={'title': 'Drag coefficient Cd'},
            hovermode='closest'
        )
    }

@app.callback(
    Output('residuals', 'figure'),
    [Input('overview', 'clickData')])
def update_figure(clickData):
    selected_Re = clickData['points'][0]['x']
    curve_number = clickData['points'][0]['curveNumber']
    trace_name = forces_dict.keys()[curve_number]
    return {
        'data': getResidualTraces(trace_name,selected_Re),
        'layout': go.Layout(
            title='Residuals for Re = '+str(selected_Re)+' ('+trace_name+')',
            xaxis={'title': 'Iterations'},
            yaxis={'title': 'Residuals', 'type': 'log'},
            hovermode='closest'
        )
    }

if __name__ == '__main__':
    app.run_server(debug=True)
