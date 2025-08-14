from dash import html, callback, Input, Output
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

from .event_table import debug_table
from .temperature_plot import make_temperature_plot


_back_button = dmc.Button(
    'Back',
    size='lg',
    variant='gradient',
    id='back-button'
)


def description(event):

    component = html.Div(
        children = [
            dmc.Group(children=[
                html.Img(src=make_temperature_plot(event)),
                debug_table(event),
                _back_button
            ], justify='flex-start', gap='10rem')
        ],
        id='event-description-container',
        style={
            'padding-block': '5px',
            'padding-inline': '1rem'
        }
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