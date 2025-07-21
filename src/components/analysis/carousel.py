from dash import clientside_callback, ClientsideFunction, Input, Output
from dash_iconify import DashIconify
import dash_mantine_components as dmc

from components import probability_plot
from components import PR_FAR_plot
from components import intensity_plot, intensity_change_plot


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
    'previousControlIcon': DashIconify(icon="icons8:up-round", width=50),
    'nextControlIcon': DashIconify(icon="icons8:down-round", width=50),
    'classNames': {
        'indicator': 'dmc-indicator',
        'control': 'dmc-control'
    }
}

_lorem_ipsum = dmc.Text(
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
     "nisi ullamcorper in. Proin placerat tristique convallis.")*10,
    id='lorem-ipsum-demo',
    style={'userSelect': 'text', 'width': '30%'},
)


def carousel(stats, task_id):

    component = dmc.Carousel([
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
                            probability_plot(stats, task_id),
                            PR_FAR_plot(stats, task_id)
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
                            intensity_plot(stats, task_id),
                            intensity_change_plot(stats, task_id)
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
                        'maxHeight': '80%',
                        'overflowY': 'auto',
                        'alignItems': 'center'
                    },
                    children=_lorem_ipsum
                )
            )
        ),
        dmc.CarouselSlide(
            dmc.Center(
                style=DEFAULT_CENTERED_SLIDE_STYLE,
                children=dmc.Text("Page 3")
            )
        ),
        dmc.CarouselSlide(
            dmc.Center(
                style=DEFAULT_CENTERED_SLIDE_STYLE,
                children=dmc.Text('Page 4')
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
        namespace='carousel',
        function_name='blockSwiper'
    ),
    Output('my-carousel', 'data-lorem-ipsum-swiper'),
    Input('lorem-ipsum-demo', 'id')
)