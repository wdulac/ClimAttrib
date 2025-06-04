from dash import html, dcc, callback, Input, Output, clientside_callback, ClientsideFunction
from dash.exceptions import PreventUpdate
from datetime import datetime as dt

from science import attribute_event
from science import plot_probability


# Fancy trick from ChatGPT to behave as if data-types were preserved
# through JSON conversion after getting stored into a dcc.Store component.
def _serialize_event(event):
    """Convertit event en un format sérialisable"""
    event_copy = event.copy()
    event_copy["date"] = event_copy["date"].isoformat()  # Convertit datetime en string ISO
    event_copy["lat_lon"] = [event_copy.pop("lat"), event_copy.pop("lon")]  # Tuple -> Liste
    return event_copy


def _deserialize_event(event):
    """Convertit event stocké en JSON en un dictionnaire avec les bons types"""
    event_copy = event.copy()
    event_copy["date"] = dt.fromisoformat(event_copy["date"])  # Reconversion ISO -> datetime
    event_copy["lat"], event_copy["lon"] = event_copy.pop("lat_lon")  # Liste -> Tuple
    return event_copy


def probability_plot(event: dict):

    serialized_event = _serialize_event(event)

    component = html.Div(children=[
        dcc.Store(id='event-data', data=serialized_event),
        dcc.Store(id='plotly-notifier-hook', data=None),
        html.Div(id='plot-container', children='Calcul en cours...')
    ], id='results-parent-container')

    return component


#~~~~~~~ Callbacks


@callback(
    Output('plot-container', 'children'),
    Input('event-data', 'data')
)
def update_result(event):

    if not event:
        raise PreventUpdate

    parsed_event = _deserialize_event(event)

    stats = attribute_event(parsed_event)
    fig = plot_probability(stats)

    return dcc.Graph(figure=fig, config=dict(displaylogo=False))


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
