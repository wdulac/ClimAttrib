from dash import register_page, html, dcc, callback, Input, Output
from dash.exceptions import PreventUpdate
import datetime as dt
from components import chosen_event
# from components import event_stats
from components import probability_plot

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

    # Read intensity in ERA5 from date
    event['intensity'] = _read_intensity_from_dates(
        event['date_start'], event['date_stop'],
        event['lat'], event['lon'],
        event['extreme_type']
    )

    return event


def _read_intensity_from_dates(
        start: dt.date, stop: dt.date,
        lat: float, lon: float,
        extreme_type: str) -> float:
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

    if extreme_type == 'hot':
        var = 'tasmax'
    elif extreme_type == 'cold':
        var = 'tasmin'

    To = xr.open_dataset(
        path_to_data_parent_dir + f"data/daily/era5_sfc_{var}_G025.nc"
    )[var].\
        sel(time=slice(start, stop + dt.timedelta(days=1))).\
        sel(lat=lat, lon=lon % 360).\
        mean('time').data

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
    query_dict = {
        "extreme_type": extreme_type,
        "method": method,
        "date": date,  
        "duration": duration,  
        "loc": loc  
    }

    # Beware not to modify the original event dict
    parsed_event = _parse_event(query_dict.copy())

    # Compose and return layout
    layout = html.Div([
        html.Div('Bienvenue sur cette page', id='analysis-welcome'),
        chosen_event(parsed_event), # Dummy component with event's description
        probability_plot(parsed_event) # Simple static img plot component
        ], className='analysis-container'
    )
    return layout