from dash import clientside_callback, ClientsideFunction, Input, Output
from dash_iconify import DashIconify
import dash_mantine_components as dmc

from components import probability_plot
from components import PR_FAR_plot

def carousel(stats):

    component = dmc.Carousel([
                    dmc.CarouselSlide(
                        dmc.Center(
                            dmc.Group(
                                children=[
                                    probability_plot(stats),
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
                            # PR_FAR_plot(stats),
                            # 'Page 2',
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
                            ),
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