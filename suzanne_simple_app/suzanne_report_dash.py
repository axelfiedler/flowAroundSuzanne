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

def loadResultFile(case,face,Re):
    # Load residual and forces files from data folder using pandas
    residuals = pd.read_csv('data/residuals_'+case+'_'+str(face)+'/Re_'+str(Re)+'.dat',
                header=1, sep='\t+', engine='python')

    forces = pd.read_csv('data/forces_'+case+'_'+str(face)+'/Re_'+str(Re)+'.dat',
                header=8, sep='\t+', engine='python')

    # Name columns of foces and residuals Dataframe
    forces.columns = ['Time', 'Cm', 'Cd', 'Cl', 'Cl_f', 'Cl_r']

    residuals.columns = ['Time', 'Ux', 'Uy', 'Uz', 'p']

    return forces, residuals

def updateResultDicts(selected_force):
    cases = []
    faces = []
    # Get a list of all files in data folder and extract the different
    # case names and mesh face numbers from the folder names
    for item in os.listdir('data'):
        cases.append(item.split('_')[1])
        faces.append(int(item.split('_')[2]))
    # Generate lists of unique case names and face numbers
    cases = list(set(cases))
    faces = list(set(faces))
    for case in cases:
        forces_dict[case] = {}
        residuals_dict[case] = {}
        final_residuals[case] = {}
        final_forces[case] = {}
        for face in faces:
            forces_dict[case][face] = {}
            residuals_dict[case][face] = {}
            final_residuals[case][face] = {}
            final_forces[case][face] = {}
            try:
                # For each case and face number extract each calculated Reynolds
                # number from the file names and load Dataframes into the variables
                # forces and residuals. Then save the Dataframes in dictionaries
                # that allow easy access to the results by case name, face number
                # and Reynolds number
                for item in os.listdir('data/residuals_'+case+'_'+str(face)):
                    Re = int(item.rpartition('_')[-1].rpartition('.')[0])
                    forces, residuals = loadResultFile(case,face,Re)
                    forces_dict[case][face][Re] = forces
                    residuals_dict[case][face][Re] = residuals
                    # Save the final results on the finest mesh in extra dictionaries
                    # to display in the overview plot
                    if face == max(faces):
                        final_residuals[case][face][Re] = residuals.tail(1)
                        final_forces[case][face][Re] = forces[selected_force].tail(1).tolist()[0]
            except:
                pass
                #print('data/residuals_'+case+'_'+str(face)+' not found.')

def getFinalForcesTraces():
    data = []
    # Loop through all cases (laminar, kEpsilon etc.) that were calculated and
    # display them as individual lines in the overview plot
    for forces_case in forces_dict:
        # From the final_forces dictionary get the keys and values to display in
        # the overview plot
        x_values = final_forces[forces_case][max(final_forces[forces_case].keys())].keys()
        y_values = final_forces[forces_case][max(final_forces[forces_case].keys())].values()
        # Sort by x values (Reynolds number)
        x_values, y_values = zip(*sorted(zip(x_values, y_values)))
        trace = go.Scatter(
        x = x_values,
        y = y_values,
        mode = 'lines+markers',
        name = forces_case,
        # Pre-select very first point
        selectedpoints = [0]
        )
        # Append the lines to the data array and return it to display
        data.append(trace)
    return data

def getConvergenceTraces(case,Re):
    data = []
    # Loop through the different mesh face numbers and append them to the data
    # array to display them as individual lines.
    for face in forces_dict[case]:
        if forces_dict[case][face]:
            trace = go.Scatter(
                x = forces_dict[case][face][Re]['Time'],
                y = forces_dict[case][face][Re][selected_force],
                mode = 'lines',
                name = str(face),
            )
            data.append(trace)
    return data

def getMeshTraces(case,Re):
    x_values = []
    y_values = []
    # If multiple meshes were calculated, get the final value that corresponds
    # to each mesh face number and append it to the x_values and y_values arrays
    # to display a line with the caluclated final values on each mesh.
    for face in forces_dict[case]:
        if forces_dict[case][face]:
            x_values.append(face)
            y_values.append(forces_dict[case][face][Re][selected_force].tail(1).tolist()[0])
    trace = [go.Scatter(
        x = x_values,
        y = y_values,
        mode = 'lines+markers'
    )]
    return trace

def getResidualTraces(case,Re):
    # Return array with residual lines for p, Ux, Uy and Uz
    trace0 = go.Scatter(
        x = residuals_dict[case][max(final_forces[case].keys())][Re]['Time'],
        y = residuals_dict[case][max(final_forces[case].keys())][Re]['p'],
        mode = 'lines',
        name = 'p'
    )
    trace1 = go.Scatter(
        x = residuals_dict[case][max(final_forces[case].keys())][Re]['Time'],
        y = residuals_dict[case][max(final_forces[case].keys())][Re]['Ux'],
        mode = 'lines',
        name = 'Ux'
    )
    trace2 = go.Scatter(
        x = residuals_dict[case][max(final_forces[case].keys())][Re]['Time'],
        y = residuals_dict[case][max(final_forces[case].keys())][Re]['Uy'],
        mode = 'lines',
        name = 'Uy'
    )
    trace3 = go.Scatter(
        x = residuals_dict[case][max(final_forces[case].keys())][Re]['Time'],
        y = residuals_dict[case][max(final_forces[case].keys())][Re]['Uz'],
        mode = 'lines',
        name = 'Uz'
    )
    data = [trace0, trace1, trace2, trace3]
    return data

# Initialize empty dictionaries that will be filled by updateResultDicts
forces_dict = {}
residuals_dict = {}

final_residuals = {}
final_forces = {}

# Choose which force coefficient should be displayed
selected_force = 'Cd'

# Fill dictionaries with results
updateResultDicts(selected_force)

app.layout = html.Div([
    html.Div([
        html.A([
            html.Div(id="logo")
        ],href='https://github.com/axelfiedler/ipost'),
        html.Div(
        id="description",
        children="This is an example of how to use Plotly Dash to generate interactive \
        plots of OpenFOAM simulation results. Shown here is the calculation to estimate \
        the drag coefficient of a flow around a monkey head using simpleFoam. Click on \
        a point in upper graph to update graphs below. For more information on the \
        problem setup click on the monkey head on the right."),
        html.A([
            html.Div(id="monkey")
        ],href='https://www.youtube.com/watch?v=lBG3qphtofE')
    ],
    id="navbar"),
    # Each plot is inside a DIV
    html.Div([
        dcc.Graph(
            id='overview',
            figure=go.Figure(
                data=getFinalForcesTraces(),
                layout=dict(
                title='Final values of '+selected_force+' vs. Reynolds number (finest mesh calculated)',
                hovermode='closest',
                xaxis={'title': 'Reynolds number'},
                yaxis={'title': selected_force},
                clickmode= 'event+select')
            )
        )
    ],className='overview-container'),
    html.Div([
        dcc.Graph(
            id='iterations',
            figure=go.Figure(
                data=getConvergenceTraces('laminar',100),
                layout=dict(
                title='Convergence of '+selected_force+' for Re = 100 (laminar)',
                xaxis={'title': 'Iterations'},
                yaxis={'title': selected_force},
                hovermode='closest',
                annotations=[
                    dict(
                        x=1.4,
                        y=1.1,
                        xref='paper',
                        yref='paper',
                        text='<b>No. of faces</b>',
                        showarrow=False
                        )
                ]
                )
            )
        )
    ],className='small-graphs-containers'),
    html.Div([
        dcc.Graph(
            id='residuals',
            figure=go.Figure(
                data= getResidualTraces('laminar',100),
                layout=dict(
                title='Residuals for Re = 100 (laminar on finest mesh)',
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
                data= getMeshTraces('laminar',100),
                layout=dict(
                title='Mesh study',
                xaxis={'title': 'No. of faces'},
                yaxis={'title': selected_force},
                hovermode='closest')
            )
        )
    ],className='small-graphs-containers')

],className='center')

# Use callback on data selection to update the three bottom plots when a point
# is selected in the overview plot
@app.callback(
    Output('iterations', 'figure'),
    [Input('overview', 'selectedData')])
def update_figure(selectedData):
    selected_Re = selectedData['points'][0]['x']
    curve_number = selectedData['points'][0]['curveNumber']
    trace_name = forces_dict.keys()[curve_number]
    return {
        'data': getConvergenceTraces(trace_name,selected_Re),
        'layout': go.Layout(
            title='Convergence of '+selected_force+' for Re = '+str(selected_Re)+' ('+trace_name+')',
            xaxis={'title': 'Iterations'},
            yaxis={'title': selected_force},
            hovermode='closest',
            annotations=[
                dict(
                    x=1.4,
                    y=1.1,
                    xref='paper',
                    yref='paper',
                    text='<b>No. of faces</b>',
                    showarrow=False
                    )
            ]
        )
    }

@app.callback(
    Output('residuals', 'figure'),
    [Input('overview', 'selectedData')])
def update_figure(selectedData):
    selected_Re = selectedData['points'][0]['x']
    curve_number = selectedData['points'][0]['curveNumber']
    trace_name = forces_dict.keys()[curve_number]
    return {
        'data': getResidualTraces(trace_name,selected_Re),
        'layout': go.Layout(
            title='Residuals for Re = '+str(selected_Re)+' ('+trace_name+' on finest mesh)',
            xaxis={'title': 'Iterations'},
            yaxis={'title': 'Residuals', 'type': 'log'},
            hovermode='closest'
        )
    }

@app.callback(
    Output('mesh', 'figure'),
    [Input('overview', 'selectedData')])
def update_figure(selectedData):
    selected_Re = selectedData['points'][0]['x']
    curve_number = selectedData['points'][0]['curveNumber']
    trace_name = forces_dict.keys()[curve_number]
    return {
        'data': getMeshTraces(trace_name,selected_Re),
        'layout': go.Layout(
            title='Mesh study for Re = '+str(selected_Re)+' ('+trace_name+')',
            xaxis={'title': 'No. of faces'},
            yaxis={'title': selected_force},
            hovermode='closest'
        )
    }

if __name__ == '__main__':
    app.run_server(debug=True)
