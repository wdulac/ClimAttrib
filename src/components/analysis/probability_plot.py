from dash import html, dcc, clientside_callback, ClientsideFunction, Input, Output
from science import plot_probability


def probability_plot(stats):

    fig = plot_probability(stats)

    component = html.Div([
        dcc.Store(id='plotly-notifier-hook', data=None),
        html.Div([
                dcc.Graph(figure=fig, config=dict(displaylogo=False))
            ],
            id='plot-container')
    ], id='results-parent-container')

    return component


# Prevent click interactions inside the plot-container from back propagating
clientside_callback(
    ClientsideFunction(
        namespace="carousel",
        function_name="blockSwiper"
    ),
    Output("plot-container", "data-dummy"),  # dummy prop
    Input("plot-container", "id")
)


# Place the plotly 'double click to zoom back out' notification relative to the
# plotly graph.
clientside_callback(
    ClientsideFunction(
        namespace='plotly_extras',
        function_name='hookPlotlyNotifier'
    ),
    Output('plotly-notifier-hook', 'data'),
    Input('plot-container', 'id'),
)