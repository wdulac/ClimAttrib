from dash import register_page, html, dcc, callback, Input, Output
from dash.exceptions import PreventUpdate
from components import chosen_event
from components import event_stats
from datetime import datetime as dt

register_page(__name__, path='/analysis')

def _parse_event(event: dict) -> dict:
    """
    Convert values from the query string to their correct data types
    """

    # Read date string as datetime object
    event['date'] = dt.strptime(event['date'], '%Y-%m-%d').date()

    # Split lat_lon string into a (lat, lon) float tuple
    _lat, _lon = [float(_) for _ in event['loc'].split('_')]
    event['lat'], event['lon'] = _lat, _lon
    # Remove original loc query parameter from event dict
    event.pop('loc')

    # Read duration as int
    event['duration'] = int(event['duration'])

    return event


def layout(extreme_type=None,
           method=None,
           date=None,
           duration=None,
           loc=None):
    """
    Note: It is good practice to catch unexpected query event here through 
    **kwargs However in our case it is already handled through redirection
    rules in utils/redirects.py
    """
    
    # parameters = locals()

    event = {
        "extreme_type": extreme_type,
        "method": method,
        "date": date,  
        "duration": str(duration),  
        "loc": loc  
    }

    parsed_event = _parse_event(event.copy())

    # Compose and return layout
    layout = html.Div([
        html.Div('Bienvenue sur cette page', id='analysis-welcome'),
        chosen_event(parsed_event),
        dcc.Store(id='event-data', data=event),
        html.Div('Calcul en cours...', id='loading-message'),
        html.Div(id='results-container')
        ], className='analysis-container'
    )
    return layout

@callback(
    Output('results-container', 'children'),
    Output('loading-message', 'children'),
    Input('event-data', 'data')
)
def compute_results(event):
    if not event:
        raise PreventUpdate
    
    event = _parse_event(event)

    test = event_stats(event).__repr__()
    return test, ""