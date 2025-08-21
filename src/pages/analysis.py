from dash import register_page, html, dcc, callback, Input, Output, State, no_update
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

import datetime as dt

import hmac, hashlib, base64, json, os

from components.analysis.event_description import description
from components.analysis.carousel import carousel

from utils.tasks import attribution

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
    
    ## Decode and validate the payload's signature
    raw = base64.urlsafe_b64decode(p + '=' * (-len(p) % 4)) # Add back trimming characters
    payload, sig = raw[:-32], raw[-32:] # Expecting 32 bytes SHA256 hash

    expected_sig = hmac.new(os.getenv('URL_SIG_SECRET_KEY').encode('utf-8'), payload, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected_sig):
        # TODO Redirect to a separate page
        return html.Div('Tampering attempt detected')
    
    event = json.loads(payload.decode('utf-8'))

    # Split and parse start and stop dates. Compute center date and duration
    start_date, stop_date = [dt.datetime.strptime(_, '%Y-%m-%d') for _ in event['dates'].split('_')]
    event['start_date'] = start_date
    event['stop_date'] = stop_date
    event['duration'] = (stop_date - start_date).days + 1
    event['date'] = event['start_date'] + (event['stop_date'] - event['start_date'])/2

    # Compose and return layout
    layout = html.Div([
        dcc.Store(data=event, id='event-data'),
        dcc.Store(data=None, id='task-id'),
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
        Output('task-id', 'data'),
        Input('event-data', 'data')
)
def run_task(data):

    if not data:
        raise PreventUpdate
    
    data['date'] = dt.datetime.fromisoformat(data['date'])

    task = attribution.apply_async(args=[data])

    return task.id
    
# TODO Find better way to retrieve stats datasets later on, than to pass task_id all the way down to create_plotly_figure
@callback(
    Output('analysis-content', 'children'),
    Output('update-interval', 'disabled'),
    Input('update-interval', 'n_intervals'),
    State('task-id', 'data'),
    State('event-data', 'data'),
    prevent_initial_call=True
)
def update_results(n, task_id, event):

    if not task_id:
        raise PreventUpdate
    
    task = attribution.AsyncResult(task_id)
    if task.ready():
        stats = task.result
        # Convert back dates to datetime objets after being serialized through the dcc.Store
        for key in ['start_date', 'stop_date', 'date']:
            if isinstance(event.get(key), str):
                event[key] = dt.datetime.fromisoformat(event[key]).date()
        return [description(event), carousel(stats, task_id)], True
    return no_update, False


