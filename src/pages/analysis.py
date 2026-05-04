"""
Analysis results page (route: ``/analysis``).

Receives the event token from the ``p`` URL query parameter, decodes and verifies it,
then renders the analysis layout in one of two modes:

**Cached result available**: retrieves the result from Redis DB 1 and renders the full
results carousel immediately. If the cached status is ``'timeout'`` (a previously
failed computation), deletes the entry and asks the user to reload.

**No cached result**: queues a Celery ``attribution`` task (expires if not started
within 5 minutes), renders a loading skeleton, and starts a ``dcc.Interval`` firing
every second. The ``update_results`` callback checks Redis on each tick; once the
cache entry appears it replaces the skeleton with the carousel and stops the interval.
After 300 ticks with no result, displays a saturation message.

The event description banner and Back button are always rendered immediately regardless
of loading state.
"""

from dash import register_page, html, dcc, callback, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

from components.analysis import (
    results_carousel,
    event_description_component
)

from app_platform.shared.tokens import decode_token
from app_platform.compute.redis import (
    make_cache_key,
    get_cache,
    cache_exists,
    delete_cache
)

# Make sure to import the Celery task named "attribution" task and not just the "attribution" function from utils.tasks
from app_platform.compute.celery import celery_app
attribution = celery_app.tasks['attribution']


TIME_TO_TASK_EXPIRY = 300 # In seconds (300 = 5 minutes)


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
        dcc.Store(data=p, id='event-token'),
        event_description_component(event)
    ], className='analysis-container', id='analysis-container')

    if cache_exists(cache_key):
        ## Retrieve cached attribution result and extend layout with the results
        
        cached_result = get_cache(cache_key)

        if cached_result['status'] == 'ok':
            # Extend the page layout with the valid attribution results
            layout.children.extend([
                dcc.Store(data=False, id='is-loading'),
                html.Div(children=results_carousel(cached_result['result'], event, cache_key),
                         id='analysis-content',
                         className='carousel-container')
            ])

        elif cached_result['status'] == 'timeout':
            # If by any chance the app retrieves a cached result that failed because of timeout,
            # delete the entry and invite the user to reload the page.
            delete_cache(cache_key)
            layout.children.extend([
                dcc.Store(data=False, id='is-loading'),
                html.Div("An error occured. Please try reloading the page in a few seconds.")
            ])

    else:
        ## Run async attribution calculation and set loading screen with 1s checks

        # Result is cached into Redis. Task is canceled if it doesn't start in under 5 minutes
        attribution.apply_async(args=(event,), expires=TIME_TO_TASK_EXPIRY)
        layout.children.extend([
            dcc.Store(data=True, id='is-loading'),
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
    Output('is-loading', 'data'),
    Input('update-interval', 'n_intervals'),
    State('cache-key', 'data'),
    State('event-token', 'data'),
    prevent_initial_call=True
)
def update_results(n, key, token):

    if n > TIME_TO_TASK_EXPIRY:
        return html.Div("The server is currently saturated. Please try again later."), True, False

    if not cache_exists(key):
        raise PreventUpdate
    
    stats = get_cache(key)
    event = decode_token(token)

    if stats['status'] == 'timeout':
        delete_cache(key)
        return html.Div("The analysis exceeded the maximum time allowed. Please try again.")

    if stats['status'] == 'ok':
        return results_carousel(stats['result'], event, key), True, False