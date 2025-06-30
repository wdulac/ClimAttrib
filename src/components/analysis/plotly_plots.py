from dash import html, dcc, clientside_callback, ClientsideFunction, Input, Output
from dash import MATCH
from science import plot_probability
from science import plot_PR_FAR
from science import plot_intensity


def intensity_plot(stats):
    fig = plot_intensity(stats)

    component = html.Div([
        html.Div(id={'type': 'plotly-notifier-hook', 'name': 'intensity'}),
        dcc.Graph(figure=fig, config=dict(displaylogo=False), id='plot-intensity')
    ], id={'type': 'plot-container', 'name': 'intensity'}, className='plot-container')

    return component


def PR_FAR_plot(stats):
    fig = plot_PR_FAR(stats)

    component = html.Div([
        html.Div(id={'type': 'plotly-notifier-hook', 'name': 'PR'}),
        dcc.Graph(figure=fig, config=dict(displaylogo=False), id='plot-PR')
    ], id={'type': 'plot-container', 'name': 'PR'}, className='plot-container')

    return component


def probability_plot(stats):

    fig = plot_probability(stats)

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