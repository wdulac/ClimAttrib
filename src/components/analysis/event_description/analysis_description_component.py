from dash import html, callback, Input, Output
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

from .event_table import debug_table
from .temperature_plot import make_temperature_plot


_back_button = dmc.Button(
    'Back',
    size='lg',
    variant='gradient',
    id='back-button',
    style={
        'margin-left': 'auto'
    }
)



def description(event):
    component = html.Div(
        children=[
            dmc.Group(
                children=[
                    # Left block
                    dmc.Group(
                        children=[
                            html.Img(src=make_temperature_plot(event)),
                            debug_table(event),
                        ],
                        gap="xl",          # contrôle espace entre plot et tableau
                        justify="flex-start" # Justify left
                    ),
                    # Back button after the left block
                    _back_button,
                ],
                justify="space-around",  # Fills up space between blocls
                grow=False,
                wrap="nowrap"
            )
        ],
        id="event-description-container",
        style={
            "padding-block": "5px",
            "padding-inline": "3rem",
        },
    )
    return component



@callback(
    Output('url', 'pathname'),
    Input('back-button', 'n_clicks'),
    prevent_initial_call=True
)
def go_home(_):

    if _:
        return "/"
    else:
        raise PreventUpdate