from dash import clientside_callback, ClientsideFunction, Input, Output
from dash_iconify import DashIconify
import dash_mantine_components as dmc

from components.analysis.plotly_plots import probability_plot
from components.analysis.plotly_plots import PR_FAR_plot
from components.analysis.plotly_plots import intensity_plot, intensity_change_plot
from components.analysis.plotly_plots import observed_Yo_with_return_levels_plot, annual_cycle_with_daily_obs_plot
from components.analysis.sentence_generator import build_summary_component


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

def carousel(stats, event, cache_key):

    component = dmc.Carousel([
        dmc.CarouselSlide(
            dmc.Center(
                style=DEFAULT_CENTERED_SLIDE_STYLE,
                children=dmc.Stack(
                    style={
                        'maxHeight': 'calc(100% - 130px)',
                        'overflowY': 'auto',
                        'width': '100%',
                        'alignItems': 'center'
                    },
                    children=build_summary_component(stats)
                )
            )
        ),
        dmc.CarouselSlide(
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
        ),
        dmc.CarouselSlide(
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
        ),
        dmc.CarouselSlide(
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
    ],
    **CAROUSEL_SETTINGS, 
    id='my-carousel' )
    
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
        namespace="carousel",
        function_name="addTooltips"
    ),
    Output("my-carousel", "data-tooltips"),  # prop factice
    Input("my-carousel", "id"),              # déclenche une seule fois
)