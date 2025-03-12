from dash import html, dcc, callback, Input, Output
from dash.exceptions import PreventUpdate
from datetime import datetime as dt

from science import compute_event_stats
from science import plot_probability

import matplotlib.pyplot as plt
import matplotlib.figure
from io import BytesIO
import base64


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


def _fig_to_uri(in_fig: matplotlib.figure.Figure, close_all=True, **save_args) -> str:
    """
    Save a figure as a URI
    :param in_fig:
    :return:
    """
    out_img = BytesIO()
    in_fig.savefig(out_img, format='png', **save_args)
    if close_all:
        in_fig.clf()
        plt.close('all')
    out_img.seek(0)  # rewind file
    encoded = base64.b64encode(out_img.read()).decode("ascii").replace("\n", "")
    return "data:image/png;base64,{}".format(encoded)


def probability_plot(event: dict):

    serialized_event = _serialize_event(event)

    component = html.Div(children=[
        dcc.Store(id='event-data', data=serialized_event),
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

    stats = compute_event_stats(parsed_event)
    fig, ax = plot_probability(stats)

    return html.Img(src=_fig_to_uri(fig))