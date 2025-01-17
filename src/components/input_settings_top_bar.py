import dash_bootstrap_components as dcc
import dash_mantine_components as dmc
from dash import html, callback, Output, Input

from datetime import datetime, date

input_settings_top_bar = html.Div(
    children=[
        html.H3("Définition de l'évènement extrême"),
        dmc.Group(children=[
            dmc.Stack(children=[
                dmc.Text("Type d'extrême", c='white', fw=700, fz=18),
                dmc.SegmentedControl(
                    id='selector:extreme-type',
                    data=[
                        "Chaud",
                        "Froid"
                    ],
                    value="Chaud"
                )],
                className='selector-with-label'
            ),
            dmc.Stack(children=[
                dmc.Text("Méthode de calcul", c='white', fw=700, fz=18),
                dmc.SegmentedControl(
                    id='selector:computation-method',
                    data=[
                        "Max. annuel",
                        "Calendaire"
                    ],
                )],
                className='selector-with-label'
            ),
            dmc.DatePickerInput(
                id='selector:date-input',
                label="Date de l'évènement",
                labelProps={
                    'c': 'white',
                    'fw': 700,
                    'fz': 18
                },
                value=datetime.now().date(),
                w=250,
                style=dict(
                    zIndex=2
                )
            ),
            dmc.Stack(children=[
                dmc.Text("Durée de l'évènement en jours", c='white', fw=700, fz=18),
                dmc.Slider(
                    id='duration-slider',
                    value=3,
                    min=1,
                    max=7,
                    restrictToMarks=True,
                    marks=[{"value": _, "label": str(_)} for _ in range(1, 8)],
                    label=None,
                    size=10,
                    classNames=dict(
                        markLabel='duration-slider-markLabel'
                    )
                )
            ],
            gap=3,
            id='slider-with-label'
            )
            ],
            id='top-bar'
        )
    ]
)