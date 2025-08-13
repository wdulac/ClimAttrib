from dash import html, dcc
import dash_mantine_components as dmc

from .event_table import debug_table
from .temperature_plot import make_temperature_plot


def test_component(event):

    component = html.Div(
        children = [
            dmc.Group(children=[
                debug_table(event),
                html.Img(src=make_temperature_plot(event))
            ])
        ],
        id='event-description-parent-container'
    )

    return component