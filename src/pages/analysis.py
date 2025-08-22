from dash import register_page, html, dcc, callback, Input, Output, State, no_update
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

import datetime as dt

import hmac, hashlib, base64, json, os, struct

from components.analysis.event_description import description
from components.analysis.carousel import carousel

from utils.tasks import attribution
from utils.url_token import decode_token
from utils.redis_cache import make_cache_key, get_cache
from utils.results import get_result

register_page(__name__, path='/analysis')


def _make_skeleton_lines(n, width='100%'):
    return [
        dmc.Skeleton(height=10, radius='xl', w=width if i == n - 1 else '100%')
        for i in range(n)
    ]


_loading_screen = [
    dmc.Box([
        dmc.Grid([
            dmc.GridCol([
                dmc.Center(dmc.Skeleton(height=350, width=600, circle=False, mb='sm', radius='sm')),
            ], span=6),

            dmc.GridCol([
                dmc.Stack(_make_skeleton_lines(10, width='70%'))
            ], span=6)
        ], gutter=100, style={'width': '100%'}, align='center'),
    ], className='loading-skeleton')
]
    

def layout(p=None):
    """
    Note: It is good practice to catch unexpected query event here through 
    **kwargs However in our case it is already handled through redirection
    rules in utils/redirects.py
    """
    
    try:
        event = decode_token(p)
    except ValueError:
        return html.Div('Tampering detected')

    # Compose and return layout
    layout = html.Div([
        dcc.Store(data=event, id='event-data'),
        dcc.Store(data=None, id='result_id'),
        dcc.Interval(
            id='update-interval',
            interval=1000,
            n_intervals=0,
            disabled=False
        ),
        html.Div(children=_loading_screen, id='analysis-content',
                 className='carousel-container')
        ], className='analysis-container', id='analysis-container'
    )
    return layout


@callback(
        Output('result_id', 'data'),
        Input('event-data', 'data')
)
def run_task(data):

    if not data:
        raise PreventUpdate
    
    data['date'] = dt.datetime.fromisoformat(data['date'])

    cache_key = make_cache_key(data)

    cached = get_cache(cache_key)

    if cached is not None:
        return f"CACHE:{cache_key}"
    
    task = attribution.apply_async(args=[data, cache_key])

    return f"TASK:{task.id}"

    
# TODO Find better way to retrieve stats datasets later on, than to pass result_id all the way down to create_plotly_figure
@callback(
    Output('analysis-content', 'children'),
    Output('update-interval', 'disabled'),
    Input('update-interval', 'n_intervals'),
    State('result_id', 'data'),
    State('event-data', 'data'),
    prevent_initial_call=True
)
def update_results(n, result_id, event):

    if not result_id:
        raise PreventUpdate
    
    stats = get_result(result_id)
    if stats is None:
        return no_update, False
    
    for key in ['start_date', 'stop_date', 'date']:
        if isinstance(event.get(key), str):
            event[key] = dt.datetime.fromisoformat(event[key]).date()
            
    return [description(event), carousel(stats, result_id)], True