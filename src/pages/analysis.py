from dash import register_page, html, dcc, callback, Input, Output
from dash.exceptions import PreventUpdate

import time
import datetime as dt
from components import chosen_event
from components import loading_screen
from components import carousel

import xarray as xr
import os

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
        chosen_event(parsed_event), # Dummy component with event's description
        html.Div(children=loading_screen, id='content',
                 className='carousel-container')
        ], className='analysis-container'
    )
    return layout


@callback(
    Output('content', 'children'),
    Input('event-data', 'data')
)
def test_page(data):

    if not data:
        raise PreventUpdate
    
    else:
        time.sleep(2)
        return carousel(data)
