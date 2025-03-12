from dash import register_page, html, dcc, callback, Input, Output
from dash.exceptions import PreventUpdate
from datetime import datetime as dt
from components import chosen_event
# from components import event_stats
from components import probability_plot

import xarray as xr
import os

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


def _read_intensity_from_date(event: dict) -> float:
    """
    TODO Docstring
    """

    current_dir = os.path.basename(os.getcwd())
    if current_dir == 'pages':
        path_to_data_parent_dir = '../../'
    elif current_dir == 'src':
        path_to_data_parent_dir = '../'
    else: # Root of the app (hopefully).
        path_to_data_parent_dir = './'

    if event['extreme_type'] == 'hot':
        var = 'tasmax'
    elif event['extreme_type'] == 'cold':
        var = 'tasmin'

    To = xr.open_dataset(
        path_to_data_parent_dir + f"data/daily/era5_sfc_{var}_G025.nc"
    )[var].\
        sel(time=event['date'], method='nearest').\
        sel(lat=event['lat'], lon=event['lon'] % 360).data

    return To    


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
    
    # Equivalent to event = locals() but more explanatory
    event = {
        "extreme_type": extreme_type,
        "method": method,
        "date": date,  
        "duration": duration,  
        "loc": loc  
    }

    # Beware not to modify the original event dict
    parsed_event = _parse_event(event.copy())
    parsed_event['event_intensity'] = _read_intensity_from_date(parsed_event)

    # Compose and return layout
    layout = html.Div([
        html.Div('Bienvenue sur cette page', id='analysis-welcome'),
        chosen_event(parsed_event), # Dummy component with event's description
        probability_plot(parsed_event) # Simple static img plot component
        ], className='analysis-container'
    )
    return layout