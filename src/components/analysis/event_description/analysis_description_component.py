from dash import html, dcc
import dash_mantine_components as dmc

from .event_table import debug_table
from .temperature_plot import make_temperature_plot


def description(event):

    component = html.Div(
        children = [
            dmc.Group(children=[
                html.Img(src=make_temperature_plot(event)),
                debug_table(event)
            ])
        ],
        id='event-description-container'
    )

    return component