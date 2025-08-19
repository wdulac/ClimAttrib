from dash import html, callback, Input, Output
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

from .event_key_figures import key_figures
from .temperature_plot import make_temperature_plot


_back_button = dmc.Button(
    'Back to event selection',
    size='lg',
    variant='gradient',
    id='back-button',
    style={
        'margin-left': 'auto',
        'margin-right': '2rem'
    }
)



def description(event):
    component = dmc.Paper(
        withBorder=True,
        p='md',
        children=[
            dmc.Group(
                children=[
                    # Left block
                    dmc.Group(
                        children=[
                            # html.Img(src=make_temperature_plot(event)),
                            key_figures(event),
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