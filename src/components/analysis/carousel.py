"""
Results carousel — main display component on the analysis page.

``results_carousel(stats, event, cache_key)`` assembles a vertical ``dmc.Carousel``
from up to four slides:

1. **Text slide** — automated text from ``sentence_generator.automated_text()``.
2. **Probability slide** — factual/counterfactual probability (pF/pC) time series
   chart and probability ratio/FAR chart, placed side by side.
3. **Intensity slide** — factual/counterfactual intensity (IF/IC) chart and intensity
   change (dI) chart, placed side by side.
4. **Observations slide** — annual extrema timeseries with estimated return levels,
   and the daily temperature for the event year against the climatology.

When ``pF == 1.0`` at the event year (meaning the event is too common to be detected
by the model), the probability and intensity slides are omitted.

Client-side callbacks (in ``assets/js/carousel.js``):

- ``carousel.toggleBounce`` — adds a bounce animation to the nav controls when a new
  slide becomes active, hinting that the carousel is scrollable.
- ``carousel.showHint`` — shows a scroll hint the first time the carousel loads.
- ``carousel.addTooltips`` — attaches tooltips to confidence-interval markers in the
  text slide.
- ``carousel.blockSwiper`` — prevents the Swiper library from intercepting mouse/touch
  events inside plot containers and the text slide.
"""

from dash import clientside_callback, callback, ClientsideFunction, Input, Output
from dash_iconify import DashIconify
import dash_mantine_components as dmc

from .__plotly_plots import (
    probability_plot,
    PR_FAR_plot,
    intensity_plot,
    intensity_change_plot,
    observed_Yo_with_return_levels_plot,
    annual_cycle_with_daily_obs_plot
)

from components.analysis.sentence_generator import automated_text


DEFAULT_SLIDE_BACKGROUND_COLOR = dmc.DEFAULT_THEME['colors']['gray'][1]

DEFAULT_CENTERED_SLIDE_STYLE = {
    'width': '100%',
    'height': '100%',
    'backgroundColor': DEFAULT_SLIDE_BACKGROUND_COLOR
}

CAROUSEL_SETTINGS = {
    'orientation': 'vertical',
    'withIndicators': True,
    'withControls': True,
    'emblaOptions': {
        'align': 'center',
        'loop': False
    },
    'previousControlIcon': DashIconify(icon="fluent:arrow-circle-up-48-regular", width=50),
    'nextControlIcon': DashIconify(icon="fluent:arrow-circle-down-48-regular", width=50),
    'classNames': {
        'indicator': 'dmc-indicator',
        'control': 'dmc-control'
    }
}

def results_carousel(stats, event, cache_key):

    automated_text_slide = dmc.CarouselSlide(
        dmc.Center(
            style=DEFAULT_CENTERED_SLIDE_STYLE,
            children=dmc.Stack(
                style={
                    'maxHeight': 'calc(100% - 130px)',
                    'overflowY': 'auto',
                    'width': '100%',
                    'alignItems': 'center'
                },
                children=automated_text(event, stats)
            )
        )
    )

    probability_slide = dmc.CarouselSlide(
        dmc.Center(
            style=DEFAULT_CENTERED_SLIDE_STYLE,
            children=dmc.Stack(
                style={
                    'maxHeight': '80%',
                    'overflowY': 'auto',
                    'width': '100%'
                },
                children=dmc.Group(
                    style={
                        'justify-content': 'space-around',
                        'align-items': 'flex-end',
                        'width': '100%',
                        'userSelect': 'none'
                    },
                    children=[
                        probability_plot(stats, cache_key),
                        PR_FAR_plot(stats, cache_key)
                    ]
                )
            )
        )
    )

    temperature_slide = dmc.CarouselSlide(
        dmc.Center(
            style=DEFAULT_CENTERED_SLIDE_STYLE,
            children=dmc.Stack(
                style={
                    'maxHeight': '100%',
                    'overflowY': 'auto',
                    'width': '100%'
                },
                children=dmc.Group(
                    style={
                        'justify-content': 'space-around',
                        'align-items': 'flex-end',
                        'width': '100%',
                        'userSelect': 'none'
                    },
                    children=[
                        intensity_plot(stats, cache_key),
                        intensity_change_plot(stats, cache_key)
                    ]
                )
            )
        )
    )

    observations_slide = dmc.CarouselSlide(
        dmc.Center(
            style=DEFAULT_CENTERED_SLIDE_STYLE,
            children=dmc.Stack(
                style={
                    'maxHeight': '100%',
                    'overflowY': 'auto',
                    'width': '100%'
                },
                children=dmc.Group(
                    style={
                        'justify-content': 'space-around',
                        'align-items': 'flex-end',
                        'width': '100%',
                        'userSelect': 'none'
                    },
                    children=[
                        observed_Yo_with_return_levels_plot(event, stats, cache_key),
                        annual_cycle_with_daily_obs_plot(event)
                    ]
                )
            )
        )
    )

    # Exclude proba/temperature slides if prob = 1.0, as chances are the temperature estimates are wrong.
    prob = float(stats['pF'].sel(time=event['date'].year, quantile='BE'))
    if prob < 1.0:
        carousel_content = [
            automated_text_slide,
            probability_slide,
            temperature_slide,
            observations_slide
        ]
    else:
        carousel_content = [
            automated_text_slide,
            observations_slide
        ]

    component = dmc.Carousel(
        children=carousel_content,
        **CAROUSEL_SETTINGS, 
        id='my-carousel' 
    )
    
    return component


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
        function_name='showHint'
    ),
    Output("my-carousel", "dummy-show-hint"),
    Input("my-carousel", "active")
)

clientside_callback(
    ClientsideFunction(
        namespace="carousel",
        function_name="addTooltips"
    ),
    Output("my-carousel", "data-tooltips"),  # prop factice
    Input("my-carousel", "id"),              # déclenche une seule fois
)