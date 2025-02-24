from dash import register_page, html
from components import chosen_event
from datetime import datetime as dt

register_page(__name__, path='/analysis')

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
    
    event = locals()
    # Read date string as datetime object
    event['date'] = dt.strptime(event['date'], '%Y-%m-%d').date()

    # Split lat_lon string into a (lat, lon) float tuple
    _lat, _lon = [float(_) for _ in loc.split('_')]
    event['lat'], event['lon'] = _lat, _lon
    # Remove original loc query parameter from event dict
    event.pop('loc')

    # Read duration as int
    event['duration'] = int(event['duration'])

    # Compose and return layout
    layout = html.Div([
        html.Div('Bienvenue sur cette page', id='analysis-welcome'),
        chosen_event(event)
        ], className='analysis-container'
    )
    return layout