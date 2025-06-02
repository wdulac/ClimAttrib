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

clientside_callback(
    ClientsideFunction(namespace="carousel", function_name="blockSwiper"),
    Output("plot-container", "data-dummy"),  # dummy prop
    Input("plot-container", "id")
)

clientside_callback(
    """
    function(input_id) {

        const parent = document.getElementById('plot-container');
        if (!parent) return window.dash_clientside.no_update;
    
        const observer = new MutationObserver(() => {
            const container = parent.querySelector('.user-select-none.svg-container')
            const notifier = document.querySelector('.plotly-notifier');
            if (container && notifier && !container.contains(notifier)) {
                container.appendChild(notifier);
                
                // Stop observing once donce
                observer.disconnect()
            }
        });

        observer.observe(document.body, { childList: true });
    
        return window.dash_clientside.no_update;
    }
    """,
    Output('plotly-notifier-hook', 'data'),
    Input('plot-container', 'id'),
)
