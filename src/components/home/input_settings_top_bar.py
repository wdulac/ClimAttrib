import dash_mantine_components as dmc
from dash import html, callback, Output, Input, State, dcc
from dash.exceptions import PreventUpdate
from .location_selector import *
import json

from datetime import datetime, timedelta, date


TOP_BAR_INPUTS_LABEL_PROPS = {
    'c': 'white',
    'fw': 700,
    'fz': 18,
}

LINK_DEFAULT_HREF = '/'

_extreme_type_segmented = dmc.Stack(children=[
    dmc.Text("Type d'extrême", **TOP_BAR_INPUTS_LABEL_PROPS),
    dmc.SegmentedControl(
        id='input:extreme-type',
        data=[
            {"value": "hot", "label": "Chaud"},
            {"value": "cold", "label": "Froid"}
        ],
        value="hot"
    )],
    className='selector-with-label'
)


_computation_method_segmented = dmc.Stack(children=[
    dmc.Text("Méthode de calcul", **TOP_BAR_INPUTS_LABEL_PROPS),
    dmc.SegmentedControl(
        id='input:computation-method',
        data= [
            {"value": "yearmax", "label": "Max. annuel"},
            {"value": "calendar", "label": "Calendaire"}
        ],
        value="yearmax"
    )],
    className='selector-with-label'
)


# TODO Merge duration selection into the calendar, e.g allow selection of a
# time range directly in the calendar component
_date_selector_calendar = dmc.DatePickerInput(
    id='input:date',
    label="Date de l'évènement",
    labelProps=TOP_BAR_INPUTS_LABEL_PROPS,
    value=date(1994, 11, 8),
    w=250,
    highlightToday=True,
    maxDate=date(2024, 12, 31),
    style=dict(
        zIndex=2
    )
)


_event_duration_slider = dmc.Stack(children=[
    dmc.Text("Durée de l'évènement en jours", **TOP_BAR_INPUTS_LABEL_PROPS),
    dmc.Slider(
        id='input:event-duration',
        value=3,
        min=1,
        max=10,
        restrictToMarks=True,
        marks=[{"value": _, "label": str(_)} for _ in [1, 2, 3, 4, 5, 6, 7, 10]],
        label=None,
        size=10,
        classNames=dict(
            markLabel='duration-slider-markLabel'
        )
    )],
    id='slider-with-label'
)

_continue_button = dcc.Link(
    children=dmc.Button(
        'Poursuivre',
        size='lg',
        variant='gradient',
        id='trigger:continue-btn'
    ),
    href=LINK_DEFAULT_HREF,
    id='dynamic-link'
)
    

debug_style = {
    "border": f"1px solid {dmc.DEFAULT_THEME['colors']['indigo'][4]}",
}

# Laying out all elements
input_settings_top_bar = html.Div(children=[
    html.H5("Définition de l'évènement extrême", id='settings-row-title'),
    dmc.Divider(variant='solid'),
    dmc.Grid(children=[
        dmc.GridCol(children=[
            dmc.Group(children=[
                _extreme_type_segmented,
                _computation_method_segmented,
                _date_selector_calendar,
                _event_duration_slider
                ], id='left-column')
            ], span=9.5),
        dmc.GridCol(children=[
            html.Div(id='button-notification-container'),
            _continue_button
        ], span='auto', id='right-column'),
    ], id='inputs-row')
], className='settings-top-bar')


#~~~~~~~ Callbacks

@callback(
    Output('button-notification-container', 'children'),
    Input('trigger:continue-btn', 'n_clicks'),
    State('input:selected-point', 'data'),
    prevent_initial_call=True
)
def notify_user(n_clicks, selected_point_data):
    """
    Notify the user to select a grid point if they try to proceed without
    having selected a grid point.
    """

    if n_clicks:
        if selected_point_data is None:
            return dmc.Notification(
                title="Oups !",
                message="Veuillez sélectionner un point de grille avant de poursuivre",
                action="show",
                autoClose=3500
            )
        else:
            raise PreventUpdate


@callback(
    Output('dynamic-link', 'href'),
    Input('input:selected-point', 'data'),
    Input('input:extreme-type', 'value'),
    Input('input:computation-method', 'value'),
    Input('input:date', 'value'),
    Input('input:event-duration', 'value')
)
def update_link(grid_point, extreme_type, computation_method, date, duration):
    """
    Update the href of the the main button based on the
    selected input settings.
    If no point is selected, the button is made inoperative.
    """
    
    if grid_point is not None:
        # Compose the href based on the input settings
        coords = json.loads(grid_point)[0]
        lat, lon = coords[0], coords[1]
        href = ("/analysis?"
                f"extreme_type={extreme_type}"
                f"&method={computation_method}"
                f"&date={date}"
                f"&duration={duration}"
                f"&loc={str(lat)}_{str(lon)}")
        
        return href
    else:
        # If no grid point is selected, revert to default href
        return LINK_DEFAULT_HREF