# -*- coding: utf-8 -*-
"""
Created on Sun Jan 27 15:48:00 2019

@author: fiedl
"""

import json
import dash
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

def loadResults(case,Re):
    residuals = pd.read_csv('data/residuals'+case+'/Re_'+str(Re)+'.dat',
                header=1, sep='\t+', engine='python')

    Cd = pd.read_csv('data/C_D'+case+'/Re_'+str(Re)+'.dat',
                header=8, sep='\t+', engine='python')

    Cd.columns = ['Time', 'Cm', 'Cd', 'Cl', 'Cl_f', 'Cl_r']

    residuals.columns = ['Time', 'Ux', 'Uy', 'Uz', 'p']

    return Cd, residuals

Re_range = np.arange(100,1200,100);

forces_dict = {}
residuals_dict = {}

final_residuals = {}
final_Cd = []

for Re in Re_range:
    forces, residuals = loadResults('_laminar',Re)
    forces_dict[Re] = forces
    residuals_dict[Re] = residuals
    final_residuals[Re] = residuals.tail(1)
    final_Cd.append(forces['Cd'].tail(1).tolist()[0])

print(final_Cd)

# for Re in Re_range:
#     print(final_forces[Re]['Cd']);

def getTraces(Re):
    trace0 = go.Scatter(
        x = residuals_dict[Re]['Time'],
        y = residuals_dict[Re]['p'],
        mode = 'lines',
        name = 'p'
    )
    trace1 = go.Scatter(
        x = residuals_dict[Re]['Time'],
        y = residuals_dict[Re]['Ux'],
        mode = 'lines',
        name = 'Ux'
    )
    trace2 = go.Scatter(
        x = residuals_dict[Re]['Time'],
        y = residuals_dict[Re]['Uy'],
        mode = 'lines',
        name = 'Uy'
    )
    trace3 = go.Scatter(
        x = residuals_dict[Re]['Time'],
        y = residuals_dict[Re]['Uz'],
        mode = 'lines',
        name = 'Uz'
    )
    data = [trace0, trace1, trace2, trace3]
    return data

app.layout = html.Div([
    html.H1(children="Flow around Blender\'s Suzanne",className='headline'),
    html.Div(
    id="description",
    children="Shows the results of a simpleFoam calculation to estimate the drag coefficient of Blender\'s Suzanne. Click on a point in upper graph to update graphs below."),
    html.Div([
        dcc.Graph(
            id='overview',
            figure=go.Figure(
                data=[
                    go.Scatter(
                    x = Re_range,
                    y = final_Cd,
                    mode = 'lines+markers',
                )],
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
                    x = forces_dict[100]['Time'],
                    y = forces_dict[100]['Cd'],
                    mode = 'lines',
                )],
                layout=dict(
                title='Convergence of Cd for Re = 100',
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
                data= getTraces(100),
                layout=dict(
                title='Residuals for Re = 100',
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
                title='Mesh study for Re = 100',
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

    return {
        'data': [go.Scatter(
            x=forces_dict[selected_Re]['Time'],
            y=forces_dict[selected_Re]['Cd'],
            mode='lines'
        )],
        'layout': go.Layout(
            title='Convergence of Cd for Re = '+str(selected_Re),
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

    return {
        'data': getTraces(selected_Re),
        'layout': go.Layout(
            title='Residuals for Re = '+str(selected_Re),
            xaxis={'title': 'Iterations'},
            yaxis={'title': 'Residuals', 'type': 'log'},
            hovermode='closest'
        )
    }

if __name__ == '__main__':
    app.run_server(debug=True)
