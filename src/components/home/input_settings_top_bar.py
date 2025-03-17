import dash_mantine_components as dmc
from dash import html, callback, Output, Input, State, dcc
from dash.exceptions import PreventUpdate
from .location_selector import *
import json

from datetime import datetime, timedelta, date

import os
import xarray as xr
import datetime as dt


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


_date_selector_calendar = dmc.DatePickerInput(
    id='input:date',
    label="Date de l'évènement",
    labelProps=TOP_BAR_INPUTS_LABEL_PROPS,
    type='range',
    value=[date(2019, 7, 24), date(2019, 7, 26)],
    allowSingleDateInRange=True,
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
    

_temperature_readout = dmc.Stack(children=[
    dmc.Text("Intensité de l'évènement sélectionné", **TOP_BAR_INPUTS_LABEL_PROPS),
    dmc.Box(id='temp-readout-field', children=None,
            fz=18, c='white', bd='solid white 1px')
], gap=0)


debug_style = {
    "border": f"1px solid {dmc.DEFAULT_THEME['colors']['indigo'][4]}",
}

# Laying out all elements
input_settings_top_bar = html.Div(children=[
    dcc.Store(id='data:intensity', data=None),
    html.H5("Définition de l'évènement extrême", id='settings-row-title'),
    dmc.Divider(variant='solid'),
    dmc.Grid(children=[
        dmc.GridCol(children=[
            dmc.Group(children=[
                _extreme_type_segmented,
                _computation_method_segmented,
                _date_selector_calendar,
                _temperature_readout
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
        Output('input:date', 'error'),
        Input('input:date', 'value'),
        prevent_initial_call=True
)
def calendar_error(dates: list):
    """
    Update the calendar's error property depending on selected date range.
    For the time being (development ungoing), the only valid range length is
    3 days
    """

    try:
        assert sum([isinstance(d, str) for d in dates]) > 0
    except AssertionError:
        # Edge case where you open the calendar, select the start of the range
        # then click out of it. Results in an empty range and dates being
        # [None, None]
        return "Date range cannot be empty"
    else:
        try:
            start, stop = [dt.datetime.strptime(_, '%Y-%m-%d').date()
                            for _ in dates]
        except TypeError:
            # Happens when the date is being picked as the second item in the
            # list is None. This isn't considered an error as the next step
            # is to either select an end date (see below), or click out
            # (see above)
            return ""
        else:
            # At this point we should have a list of two datetime objects.
            # We evaluate the duration in days between start and stop date
            duration = ((stop - start) + dt.timedelta(days=1)).days
            
            if duration != 3:
                return "Please select a day time range"
            else:
                return ""


@callback(
        Output('temp-readout-field', 'children'),
        Output('data:intensity', 'data'),
        Input('input:selected-point', 'data'),
        Input('input:extreme-type', 'value'),
        Input('input:date', 'value'),
)
def update_temperature(grid_point: str, extreme_type: str, date: list) -> str:
    if not None in date:
        if grid_point is not None:
            lat, lon = json.loads(grid_point)[0]
            start, stop = [dt.datetime.strptime(_, '%Y-%m-%d').date()
                            for _ in date]
            if extreme_type == 'hot':
                var = 'tasmax'
            elif extreme_type == 'cold':
                var = 'tasmin'
            To = xr.open_dataset(f"./data/daily/era5_sfc_{var}_G025.nc")[var].\
                sel(
                    time=slice(start, stop + dt.timedelta(days=1)),
                    lat=lat, lon=lon % 360
                ).\
                mean('time').data
            return f"{To-273.15:.1f}°C", f"{To:.2f}"
        return "Select a grid point", None
    else:
        return "Select a date range", None


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
    State('input:selected-point', 'data'),
    Input('input:extreme-type', 'value'),
    Input('input:computation-method', 'value'),
    State('input:date', 'value'),
    Input('input:date', 'error'),
    Input('data:intensity', 'data')
)
def update_link(
    grid_point: str, # JSON serialized
    extreme_type: str,
    computation_method: str,
    date: list,
    date_error: str,
    intensity: str #JSON serialized
) -> str:
    """
    Update the href of the the main button based on the
    selected input settings.
    If no point is selected, the button is made inoperative.
    A valid time range is required to produce a valid href
    """
    
    if not date_error:
        if grid_point is not None:
            # Compose the href based on the input settings
            coords = json.loads(grid_point)[0]
            lat, lon = coords[0], coords[1]
            To = json.loads(intensity)
            href = ("/analysis?"
                    f"extreme_type={extreme_type}"
                    f"&method={computation_method}"
                    f"&date={date[0].__str__()}_{date[1].__str__()}"
                    f"&To={To}"
                    f"&loc={str(lat)}_{str(lon)}")
            
            return href
        else:
            # If no grid point is selected, revert to default href
            return LINK_DEFAULT_HREF
    else:
        return LINK_DEFAULT_HREF