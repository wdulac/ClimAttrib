from dash import register_page, html, dcc, callback, Input, Output
from dash import clientside_callback, ClientsideFunction
from dash.exceptions import PreventUpdate

import dash_mantine_components as dmc
from dash_iconify import DashIconify

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
                                        ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris sed ipsum ut ",
                                         "tellus tincidunt ullamcorper at eu metus. Phasellus et mi auctor, molestie "
                                         "sapien ut, vulputate nisl. Etiam non est vestibulum nibh commodo pulvinar. "
                                         "Quisque vulputate commodo tellus nec malesuada. Praesent a semper massa. "
                                         "Aliquam tortor risus, dapibus eget vestibulum vel, rutrum quis lorem. "
                                         "Vivamus ut cursus nunc. Morbi sit amet rhoncus urna. Quisque volutpat a orci "
                                         "quis tincidunt. Nullam euismod dictum turpis eget sagittis. Aenean facilisis "
                                         "est arcu, ac tincidunt ipsum lobortis vitae. Curabitur a enim tristique, "
                                         "maximus erat sed, pharetra lorem. Proin laoreet congue porttitor. Donec "
                                         "luctus justo semper ex varius tristique. In ultrices lacus est, a rhoncus "
                                         "nisi ullamcorper in. Proin placerat tristique convallis."),
                                        id='lorem-ipsum-demo',
                                        style={'userSelect': 'text'},
                                        w=600
                                    )
                                ],
                            h='100%', style={
                                'justifyContent': 'space-around',
                                'width': '100%',
                                'userSelect': 'none'
                                }
                            ),
                        h='100%', bg=dmc.DEFAULT_THEME['colors']['yellow'][2]
                        )
                    ),
                    dmc.CarouselSlide(
                        dmc.Center(
                            "Page 2",
                            bg=dmc.DEFAULT_THEME['colors']['red'][2], c="black", w="100%", h="100%"
                        )
                    ),
                    dmc.CarouselSlide(
                        dmc.Center(
                            "Page 3",
                            bg=dmc.DEFAULT_THEME['colors']['green'][2], c='black', w='100%', h='100%'
                        )
                    ),
                    dmc.CarouselSlide(
                        dmc.Center(
                            "Page 4",
                            bg=dmc.DEFAULT_THEME['colors']['blue'][2], c='black', w='100%', h='100%'
                        )
                    )
                ],
                orientation='vertical',
                withIndicators=True,
                withControls=True,
                emblaOptions={
                    'align': 'center',
                    'loop': False
                },
                previousControlIcon=DashIconify(icon="icons8:up-round", width=50),
                nextControlIcon=DashIconify(icon="icons8:down-round", width=50),
                classNames={
                    "indicator": "dmc-indicator",
                    "control": "dmc-control"
                },
                id='my-carousel'
                )
            ], className='carousel-container'),
        ], className='analysis-container'
    )
    return layout

clientside_callback(
    ClientsideFunction(
        namespace='carousel',
        function_name='toggleBounce'
    ),
    Output("my-carousel", "data-toggle-bounce"),
    Input("my-carousel", "active")
)

clientside_callback(
    ClientsideFunction(
        namespace='carousel',
        function_name='blockSwiper'
    ),
    Output('my-carousel', 'data-lorem-ipsum-swiper'),
    Input('lorem-ipsum-demo', 'id')
)