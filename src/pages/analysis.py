from dash import register_page, html, dcc, callback, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

from components.analysis.event_description import description
from components.analysis.carousel import carousel

from utils.tasks import attribution
from utils.url_token import decode_token
from utils.redis_cache import make_cache_key, get_cache, cache_exists


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
    
    try:
        event = decode_token(p)
    except ValueError:
        return html.Div('Tampering detected')
    
    cache_key = make_cache_key(event)

    # Initialise layout with the event's description
    layout = html.Div(children=[
        description(event)
    ], className='analysis-container', id='analysis-container')

    if cache_exists(cache_key):
        # Retrieve cached attribution result and extend layout with the results
        cached_result = get_cache(cache_key)
        
        layout.children.extend([
            html.Div(children=carousel(cached_result, cache_key),
                     id='analysis-content',
                     className='carousel-container')
        ])

    else:
        # Run async attribution calculation and set loading screen with 1s checks
        attribution.apply_async(args=[event, cache_key])

        layout.children.extend([
            dcc.Store(data=cache_key, id='cache-key'),
            dcc.Interval(
                id='update-interval',
                interval=1000,
                n_intervals=0,
                disabled=False
            ),
            html.Div(children=_loading_screen, id='analysis-content',
                     className='carousel-container')
        ])

    return layout

    
# TODO Find better way to retrieve stats datasets later on, than to pass cache_key all the way down to create_plotly_figure
@callback(
    Output('analysis-content', 'children'),
    Output('update-interval', 'disabled'),
    Input('update-interval', 'n_intervals'),
    State('cache-key', 'data'),
    prevent_initial_call=True
)
def update_results(n, key):

    if not cache_exists(key):
        raise PreventUpdate
    
    stats = get_cache(key)
    return carousel(stats, key), True