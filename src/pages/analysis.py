from dash import register_page, html, dcc, callback, Input, Output, State, no_update
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

import datetime as dt
from components.analysis.chosen_event import chosen_event
from components.analysis.carousel import carousel

from utils.tasks import attribution

register_page(__name__, path='/analysis')

def _parse_event(query: dict) -> dict:
    """
    Convert values from the query string to their correct data types
    """

    event = dict()

    event['method'], event['extreme_type'] = query['method'], query['extreme_type']

    # Read date string as datetime object
    event['date_start'], event['date_stop'] = [
        dt.datetime.strptime(_, '%Y-%m-%d').date() for _ in query['date'].split('_')
    ]

    # Evaluate middle date
    event['date'] = event['date_start'] + (event['date_stop'] - event['date_start'])/2

    # Evaluate event duration in days
    event['duration'] = (event['date_stop'] - event['date_start']).days + 1

    # Split lat_lon string into a (lat, lon) float tuple
    event['lat'], event['lon'] = [float(_) for _ in query['loc'].split('_')]

    # Parse query intensity into float
    event['intensity'] = float(query['To'])

    return event


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


def layout(extreme_type=None,
           method=None,
           date=None,
           To=None,
           loc=None):
    """
    Note: It is good practice to catch unexpected query event here through 
    **kwargs However in our case it is already handled through redirection
    rules in utils/redirects.py
    """
    
    # Equivalent to event = locals() but more explanatory
    query_dict = {
        "extreme_type": extreme_type,
        "method": method,
        "date": date,  
        "To": To,  
        "loc": loc  
    }

    # Beware not to modify the original event dict
    parsed_event = _parse_event(query_dict.copy())

    # Compose and return layout
    layout = html.Div([
        dcc.Store(data=parsed_event, id='event-data'),
        dcc.Store(data=None, id='task-id'),
        dcc.Interval(
            id='update-interval',
            interval=1000,
            n_intervals=0,
            disabled=False
        ),
        chosen_event(parsed_event), # Dummy component with event's description
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
    prevent_initial_call=True
)
def update_results(n, task_id):

    if not task_id:
        raise PreventUpdate
    
    task = attribution.AsyncResult(task_id)
    if task.ready():
        stats = task.result
        return carousel(stats, task_id), True
    return no_update, False


