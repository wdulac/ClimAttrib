from dash import register_page, html, dcc, callback, Input, Output
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
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
        # html.Div('Bienvenue sur cette page', id='analysis-welcome'),
        chosen_event(parsed_event), # Dummy component with event's description
        html.Div([
            dmc.Carousel([
                    dmc.CarouselSlide(
                        dmc.Center(
                            dmc.Group(
                                children=[
                                    probability_plot(parsed_event),
                                    dmc.Text(
                                        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                                        "Vestibulum eget velit non ipsum dignissim feugiat.",
                                        w=400  # largeur fixe ou ajustable selon besoin
                                    )
                                ],
                            h='100%', style={'justifyContent': 'space-around', 'width': '100%'}
                            ),
                        h='100%', bg='yellow'
                        )
                    ),
                    dmc.CarouselSlide(
                        dmc.Center("Test", bg="green", c="white", w="100%", h="100%")
                    )
                ],
                align='center',
                orientation='vertical',
                withIndicators=True,
                withControls=True,
                loop=False,
                classNames={"indicator": "dmc-indicator"}
                )
            ], className='carousel-container')
        ], className='analysis-container'
    )
    return layout