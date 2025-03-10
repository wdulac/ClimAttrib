from dash import register_page, html, dcc, callback, Input, Output
from dash.exceptions import PreventUpdate
from datetime import datetime as dt
from components import chosen_event
# from components import event_stats
from components import probability_plot

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

    # Compose and return layout
    layout = html.Div([
        html.Div('Bienvenue sur cette page', id='analysis-welcome'),
        chosen_event(parsed_event), # Dummy component with event's description
        dcc.Store(id='event-data', data=event), # Serialize dict into JSON
        html.Div('Calcul en cours...', id='loading-message'),
        # Use empty div for the results so that the page can load before
        # running the calculation
        html.Div(id='results-container')
        ], className='analysis-container'
    )
    return layout


#~~~~~~~ Callbacks


@callback(
    Output('results-container', 'children'),
    Output('loading-message', 'children'),
    Input('event-data', 'data')
)
def compute_results(event):
    """
    Trigger computation once the page has loaded and the event's data has been
    stored into memory.

    Return stats into `results-container` div and remove the "loading" message.
    """

    if not event:
        raise PreventUpdate
    
    event = _parse_event(event)
    # stats = event_stats(event).__repr__()
    fig = probability_plot(event)

    return fig, ""