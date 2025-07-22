from dash import html, dcc, clientside_callback, ClientsideFunction, Input, Output
from dash import MATCH
from science import plot_probability
from science import plot_PR_FAR
from science import plot_intensity
from science import plot_intensity_change


def intensity_change_plot(stats, task_id):
    fig = plot_intensity_change(stats, task_id)

    component = html.Div([
        html.Div(id={'type': 'plotly-notifier-hook', 'name': 'dI'}),
        dcc.Graph(figure=fig, config=dict(displaylogo=False), id='plot-intensity-change')
    ], id={'type': 'plot-container', 'name': 'delta-intensity'}, className='plot-container')

    return component


def intensity_plot(stats, task_id):
    fig = plot_intensity(stats, task_id)

    component = html.Div([
        html.Div(id={'type': 'plotly-notifier-hook', 'name': 'intensity'}),
        dcc.Graph(figure=fig, config=dict(displaylogo=False), id='plot-intensity')
    ], id={'type': 'plot-container', 'name': 'intensity'}, className='plot-container')

    return component


def PR_FAR_plot(stats, task_id):
    fig = plot_PR_FAR(stats, task_id)

    component = html.Div([
        html.Div(id={'type': 'plotly-notifier-hook', 'name': 'PR'}),
        dcc.Graph(figure=fig, config=dict(displaylogo=False), id='plot-PR')
    ], id={'type': 'plot-container', 'name': 'PR'}, className='plot-container')

    return component


def probability_plot(stats, task_id):
    fig = plot_probability(stats, task_id)

    component = html.Div([
        html.Div(id={'type': 'plotly-notifier-hook', 'name': 'probability'}),
        dcc.Graph(figure=fig, config=dict(displaylogo=False), id='plot-probability')
    ], id={'type': 'plot-container', 'name': 'probability'}, className='plot-container')

    return component


# Prevent click interactions inside the plot-container from back propagating
clientside_callback(
    ClientsideFunction(
        namespace="carousel",
        function_name="blockSwiper"
    ),
    Output({"type": "plot-container", "name": MATCH}, "data-dummy"),  # dummy prop
    Input({"type": "plot-container", "name": MATCH}, "id")
)


# Place the plotly 'double click to zoom back out' notification relative to the
# plotly graph.
# clientside_callback(
#     ClientsideFunction(
#         namespace='plotly_extras',
#         function_name='hookPlotlyNotifier'
#     ),
#     Output({'type': 'plotly-notifier-hook', 'name': MATCH}, 'data-dummy'),
#     Input({'type': 'plot-container', 'name': MATCH}, 'id'),
# )


clientside_callback(
    ClientsideFunction(
        namespace='plotly_extras',
        function_name='addButtonsToModebar'
    ),
    Output({'type': 'plot-container', 'name': MATCH}, 'data-dummy2'),  # dummy prop, just trigger
    Input({'type': 'plot-container', 'name': MATCH}, 'id'),
)