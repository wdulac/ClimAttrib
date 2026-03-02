"""
# Module overview

This module implements the top settings bar used to select extreme-event inputs
for the attribution application. It builds a Dash / Dash-Mantine UI containing
controls for event type, date selection, computation method, a temperature
readout, and a primary "Continue" action. Several callbacks keep the UI
consistent, validate user inputs, compute a brief temperature summary from
on-disk NetCDF resources, and generate a signed navigation token.

## Primary features

- UI components:
    - Segmented control to choose extreme type (`hot` / `cold`).
    - Segmented control to choose computation method ("Restrict to same dates":
        `calendar` or `yearmax`).
    - Date range picker (`dmc.DatePickerInput`) with validation/enforced allowed
        durations and a JS hook to dynamically disable invalid ranges.
    - Temperature readout group showing observed intensity, anomaly, anomaly
        icon, and climatology quantiles.
    - Continue button wrapped in a `dcc.Link` whose `href` is updated by inputs.
    - `dcc.Store` component `data:intensity` used to persist computed intensity.

- Static resources loaded at module import:
    - Several Markdown files (help/tooltips) read from `RESOURCES`.
    - Icons configured via `DashIconify` and local constants for arrow/minus icons.

- Constants:
    - `ALLOWED_DURATIONS`: list of valid time-window lengths in days (default:
        `[1, 2, 3, 4]`).
    - `LINK_DEFAULT_HREF`: fallback URL used when inputs are incomplete.

## Callbacks (behavior summary)

### 1) `update_disabled_dates(date_range)`
- Output: `input:date.disabledDates`
- Purpose: When the user selects a date range, returns a structure with a
    `"function"` key (`"disableInvalidRange"`) and `options` describing allowed
    durations and the current start/end. This leverages DMC's client-side
    feature to disable invalid end/start dates.

### 2) `calendar_error(dates: list) -> str`
- Output: `input:date.error`
- Purpose: Validate date selections and return human-friendly error messages.
    Handles partial selections (e.g. `[start, None]`) and empty-range edge cases.
    Enforces `ALLOWED_DURATIONS` and returns an appropriate error string or an
    empty string on success.

### 3) `update_temperature(grid_point, extreme_type, date, date_error)`
- Outputs:
    - `temp-readout-value.children` (observed mean temperature string in °C)
    - `temp-readout-anomaly.children` (anomaly string in °C)
    - `temp-readout-anomaly-icon.children` (icon: up / down / minus)
    - `temp-readout-clim.children` (climatology quantiles string in °C)
    - `data:intensity.data` (numeric intensity stored as a serialized string)
- Purpose: Given a selected grid point and validated date range, opens two
    NetCDF datasets (observations and smoothed daily climatology) via xarray,
    computes the mean observed temperature over the selected dates, looks up the
    corresponding climatological quantiles by day-of-year, computes the anomaly,
    and returns formatted UI strings and a stored intensity value.
- Notes:
    - Input NetCDF values are in Kelvin; displayed values are converted to °C by
        subtracting 273.15.
    - Anomaly thresholds for icons: >= +0.5 (up arrow), <= -0.5 (down arrow),
        otherwise neutral (minus icon).
    - This callback opens NetCDF files on disk (`DATA/daily/...` and
        `DATA/annual_cycle/...`) and may be I/O / memory intensive. Consider
        caching or lazy-loading for production.

### 4) `notify_user(n_clicks, selected_point_data)`
- Output: `notification-container.sendNotifications`
- Purpose: When the Continue button is clicked without a selected grid point,
    emit a notification instructing the user to choose a point. If a point is
    present, raise `PreventUpdate`.

### 5) `update_link(grid_point, extreme_type, computation_method, date, date_error, intensity)`
- Output: `dynamic-link.href`
- Purpose: Compose a signed URL token (via `utils.url_token.encode_token`)
    encoding the input settings (`extreme_type`, `computation_method`, `date` range,
    `lat`/`lon`, `intensity`) and set the Continue button's href to navigate to
    the analysis page (`/analysis?p=<token>`).
- Validation: Returns the default fallback href when the date is invalid, the
    grid point is missing, or required inputs are not ready.

## Important component ids and stores

- `input:extreme-type` (SegmentedControl)
- `input:computation-method` (SegmentedControl)
- `input:date` (dmc.DatePickerInput)
- `input:selected-point` (expected elsewhere in the app; a JSON-serialized
    `[lat, lon]` pair)
- `temp-readout-value`, `temp-readout-anomaly`,
    `temp-readout-anomaly-icon`, `temp-readout-clim` (UI elements)
- `data:intensity` (`dcc.Store` used to persist computed intensity)
- `trigger:continue-btn` (Button nested inside `dynamic-link`)
- `dynamic-link` (Link wrapping the Continue button)
- `notification-container` (component that accepts `sendNotifications` payloads)

## Dependencies and side effects

- Relies on `dash`, `dash_mantine_components`, `dash_iconify`, `dcc`, `html`,
    `xarray`, and local utilities `utils.url_token` and `utils.paths`.
- Reads textual tooltip Markdown files from `RESOURCES` at import time.
- Reads NetCDF datasets from `DATA` within the `update_temperature` callback.
- Uses a small JS-side DatePicker helper (`disableInvalidRange`) through DMC's
    `disabledDates` mechanism; that client-side function must be available for
    full UX enforcement of allowed durations.

## Usage

Import the module and include the exported layout fragment
(`input_settings_top_bar`) into the Dash application layout. The callbacks
assume certain other app-level components exist (notably `input:selected-point`
and `notification-container`). Ensure the `DATA` and `RESOURCES` paths resolve
to the expected NetCDF and Markdown files, and that `encode_token` is available
to sign navigation tokens.

## Error handling

- Callbacks return user-visible validation strings where appropriate and use
    `PreventUpdate` to avoid unnecessary updates.
- `update_temperature` wraps climatology quantile extraction in a `try/except`
    and falls back to `NaN` values if quantiles cannot be read for the selected
    coordinates/days.

## Extensibility notes

- `ALLOWED_DURATIONS` is a module-level constant and can be adjusted without
    changing callback logic; ensure client-side `disableInvalidRange` logic is
    kept in sync with this list.
- For production, consider caching opened datasets or using lazy/delayed
    loading to reduce per-callback I/O. Also validate and securely handle the
    `encode_token` inputs if exposed externally.
"""

from dash import html, callback, Output, Input, State, dcc
from dash import get_relative_path
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from dash_iconify import DashIconify

import xarray as xr
import datetime as dt
import os

import json
from app_platform.shared.tokens import encode_token
from app_platform.shared.paths import DATA
from app_platform.shared.urls import URL_PREFIX_DASH
from components.resources import (
    COMPUTE_TOOLTIP_CONTENT,
    ANOMALY_TOOLTIP_CONTENT,
    CLIMATOLOGY_TOOLTIP_CONTENT
)

from science.attribution.__calendar_utils import _datetime_to_doy

TOP_BAR_INPUTS_LABEL_PROPS = {
    'c': 'white',
    'fw': 700,
    'fz': 18,
}

LINK_DEFAULT_HREF = URL_PREFIX_DASH

ALLOWED_DURATIONS = [1, 2, 3, 4, 5, 7, 10, 14] # In days

CALENDAR_MIN_DATE = dt.date(1940, 1, 1)
CALENDAR_MAX_DATE = dt.date.fromisoformat(os.getenv("CALENDAR_MAX_DATE", "20221231"))

## Icons
MINUS_ICON = DashIconify(icon="mdi:minus", width=20, style={"position": "relative", "top": "4px"})
ARROW_UP_ICON = DashIconify(icon="mdi:arrow-up-bold", width=20, style={"position": "relative", "top": "4px"})
ARROW_DOWN_ICON = DashIconify(icon="mdi:arrow-down-bold", width=20, style={"position": "relative", "top": "4px"})

## Helper functions

def _help_tooltip_hovercard(CONTENT: str) -> dmc.HoverCard:
    """
    Return a preconfigured dmc.HoverCard help tooltip that renders CONTENT as Markdown.
    """

    return dmc.HoverCard(
        withArrow=True,
        arrowSize=15,
        width=250,
        shadow='md',
        children=[
            dmc.HoverCardTarget(
                DashIconify(icon="material-symbols:help-outline", width=17,
                style={"position": "relative", "top": "4px"})
            ),
            dmc.HoverCardDropdown([
                dcc.Markdown(CONTENT),
            ], className='tooltip-markdown')
        ]
    )

## Building individual components

# Hot / cold selector
_extreme_type_segmented = dmc.Stack(children=[
    dmc.Text("Extreme type", **TOP_BAR_INPUTS_LABEL_PROPS),
    dmc.SegmentedControl(
        id='input:extreme-type',
        data=[
            {"value": 'hot', "label": "Hot"},
            {"value": 'cold', "label": "Cold"}
        ],
        value='hot',
        persistence=True,
        persistence_type='session',
    )],
    className='selector-with-label'
)

# Annual max / calendar selector
_computation_method_segmented = dmc.Stack(children=[
    dmc.Group(children=[
        dmc.Text("Restrict to same dates", **TOP_BAR_INPUTS_LABEL_PROPS),
        _help_tooltip_hovercard(COMPUTE_TOOLTIP_CONTENT)
    ], gap='sm'),
    dmc.SegmentedControl(
        id='input:computation-method',
        data= [
            {"value": "calendar", "label": "Yes"},
            {"value": "yearmax", "label": "No"},
        ],
        value="yearmax",
        persistence=True,
        persistence_type='session',
    )],
    className='selector-with-label'
)

# Date picker
_date_selector_calendar = dmc.DatePickerInput(
    id='input:date',
    label="Event date(s)",
    labelProps=TOP_BAR_INPUTS_LABEL_PROPS,
    type='range',
    value=[dt.date(2019, 7, 23), dt.date(2019, 7, 25)],
    allowSingleDateInRange=True,
    w=300,
    highlightToday=False,
    weekendDays=[],
    minDate=CALENDAR_MIN_DATE,
    maxDate=CALENDAR_MAX_DATE,
    persistence=True,
    persistence_type='session',
    disabledDates={"function": "disableInvalidRange", "options": None},
    className='datepicker-container'
)

# Continue button
_continue_button = dcc.Link(
    children=dmc.Button(
        'Continue',
        size='lg',
        variant='gradient',
        id='trigger:continue-btn'
    ),
    href=LINK_DEFAULT_HREF,
    id='dynamic-link'
)
    
# Temperature readout field
_temperature_readout = dmc.Group(
    children=[
        # Main temperature intensity readout element
        dmc.Stack(children=[
            dmc.Text('Intensity', **TOP_BAR_INPUTS_LABEL_PROPS),
            dmc.Text(id='temp-readout-value', children=None, fz=18, c='white')
        ], gap='3px'),

        dmc.Divider(orientation='vertical', size='xs'),

        # Anomaly element with dropdown hovercard
        dmc.Stack(children=[
            dmc.Group(children=[
                dmc.Text('Anomaly', **TOP_BAR_INPUTS_LABEL_PROPS),
                _help_tooltip_hovercard(ANOMALY_TOOLTIP_CONTENT)
            ], gap='xs'),
            dmc.Group(children=[
                dmc.Box(id='temp-readout-anomaly-icon', children=MINUS_ICON, p=0),
                dmc.Text(id='temp-readout-anomaly', children=None, fz=18, c='white')
            ], gap='xs', align='center', wrap="nowrap")
        ], gap='3px', style={'minHeight': 56.8}),

        # Climatology element with dropdown hovercard
        dmc.Stack(children=[
            dmc.Group(children=[
                dmc.Text('Climatology', **TOP_BAR_INPUTS_LABEL_PROPS),
                _help_tooltip_hovercard(CLIMATOLOGY_TOOLTIP_CONTENT)
            ],gap='xs'),
            dmc.Text(id='temp-readout-clim', children=None, fz=18, c='white')
        ], gap='3px', style={'minHeight': 55.7})
    ],
    justify='center',
    align='center',
    gap='md',
    grow=False,
    wrap="nowrap",
    style={'minWidth': '433px'}
)

# Laying out all elements
event_definition_component = html.Div(children=[
    dcc.Store(id='data:intensity', data=None),
    html.H3("Extreme event selection", id='settings-row-title'),
    dmc.Divider(variant='solid'),
    dmc.Grid(children=[
        dmc.GridCol(children=[
            dmc.Group(children=[
                _extreme_type_segmented,
                _date_selector_calendar,
                _computation_method_segmented,
                _temperature_readout
                ], id='left-column')
            ], span=9.5),
        dmc.GridCol(children=[
            _continue_button
        ], span='auto', id='right-column'),
    ], id='inputs-row')
], className='settings-top-bar')


#~~~~~~~ Callbacks

@callback(
    Output('input:date', 'disabledDates'),
    Input('input:date', 'value'),
    prevent_initial_call=True
)
def update_disabled_dates(date_range):
    """
    Pass the current selected dates (even if None) to the JS function that
    decides which date to disable to enforce ALLOWED_DURATIONS.
    
    This is made possible since the DMC 2.0 release
    """

    if date_range:
        return {
            "function": "disableInvalidRange",
            "options": {
                "validDurations": ALLOWED_DURATIONS,
                "startDate": date_range[0],
                "endDate": date_range[1]
            }
        }
    else:
        raise PreventUpdate


@callback(
        Output('input:date', 'error'),
        Input('input:date', 'value'),
        prevent_initial_call=False
)
def calendar_error(dates: list):
    """
    Update the calendar's error property depending on selected date range.
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
            # Note : This is legacy code and should likely never be needed anymore
            # since the calendar dynamically disables dates for unallowed durations
            duration = ((stop - start) + dt.timedelta(days=1)).days
            
            if duration not in ALLOWED_DURATIONS:
                return "Please select a valid time range"
            else:
                return ""


@callback(
        Output('temp-readout-value', 'children'),
        Output('temp-readout-anomaly', 'children'),
        Output('temp-readout-anomaly-icon', 'children'),
        Output('temp-readout-clim', 'children'),
        Output('data:intensity', 'data'),
        Input('input:selected-point', 'data'),
        Input('input:extreme-type', 'value'),
        Input('input:date', 'value'),
        Input('input:date', 'error')
)
def update_temperature(grid_point: str, extreme_type: str, date: list,
                        date_error):
    """
    Compute observed mean temperature over selected dates and compare to
    the smoothed annual cycle climatology. Returns small UI pieces and stores.
    """
    if None in date:
        # incomplete selection
        return ("Select a date range", "", MINUS_ICON, "", None)

    if date_error:
        return ("Select a valid date range", "", MINUS_ICON, "", None)

    if grid_point is None:
        return ("Select a grid point", "", MINUS_ICON, "", None)

    # parse inputs -> use dt.datetime objects (required by _datetime_to_doy)
    start_dt, stop_dt = [dt.datetime.strptime(_, '%Y-%m-%d') for _ in date]

    lat, lon = json.loads(grid_point)

    # Observed ERA5 daily file (intensity)
    era5_path = DATA / 'daily' / 'era5_sfc_daily_tas.nc'
    ds_obs = xr.open_dataset(era5_path)
    # select time slice: include stop day (xarray slice is inclusive for datetime)
    To_da = ds_obs['tas'].sel(time=slice(start_dt, stop_dt + dt.timedelta(days=1)),
                              lat=lat, lon=lon % 360)
    # mean over time
    To_val = float(To_da.mean('time').data)

    # Annual cycle climatology file (smoothed daily quantiles)
    cyc_path = DATA / 'annual_cycle' / 'ERA5_120x240_smoothed_daily_annual_cycle_1991-2020.nc'
    ds_cyc = xr.open_dataset(cyc_path)

    # Build list of day-of-year using the exact helper from attribution.py
    n_days = (stop_dt.date() - start_dt.date()).days + 1
    selected_dts = [start_dt + dt.timedelta(days=i) for i in range(n_days)]
    doy_list = [_datetime_to_doy(d) for d in selected_dts]

    # Select days and lat/lon from climatology and average over dayofyear
    # ds_cyc['tas'] dims: (dayofyear, lat, lon, quantile)
    cyc_sel = ds_cyc['tas'].sel(dayofyear=doy_list, lat=lat, lon=lon % 360)
    cyc_mean = cyc_sel.mean('dayofyear')

    # Extract quantiles (strings like '10%', '50%', '90%')
    try:
        q10 = float(cyc_mean.sel(quantile='10%').data)
        median = float(cyc_mean.sel(quantile='50%').data)
        q90 = float(cyc_mean.sel(quantile='90%').data)
    except Exception:
        # If selection failed, fallback to NaNs
        q10 = median = q90 = float('nan')

    # anomaly (K) -> same magnitude in °C
    anomaly = To_val - median
    anomaly_c = anomaly  # in °C-equivalent

    # Decide icon and color qualitatively
    if anomaly_c >= 0.5:
        icon = ARROW_UP_ICON
        anom_text = f"+{anomaly_c:.1f}°C"
    elif anomaly_c <= -0.5:
        icon = ARROW_DOWN_ICON
        anom_text = f"{anomaly_c:.1f}°C"
    else:
        icon = MINUS_ICON
        anom_text = f"{anomaly_c:.1f}°C"

    # prepare small climatology string
    clim_text = f"{q10-273.15:.1f}°C / {median-273.15:.1f}°C / {q90-273.15:.1f}°C"

    # display observed temp in °C
    temp_text = f"{To_val-273.15:.1f}°C"

    return temp_text, anom_text, icon, clim_text, f"{To_val:.2f}"


@callback(
    Output('notification-container', 'sendNotifications'),
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
            return [{
                "action": "show",
                "title": "Oops !",
                "message": "Please select a grid point before proceeding",
                "autoClose": 3500
            }]
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
    if not None in date:
        if not date_error:
            if grid_point is not None:
                # Compose the href based on the input settings
                coords = json.loads(grid_point)
                lat, lon = coords[0], coords[1]
                To = json.loads(intensity)

                # Create signed URL token
                token = encode_token(extreme_type, computation_method, date, lat, lon, To)

                # Create and return href
                href = get_relative_path(f"/analysis?p={token}")
                
                return href
            else:
                # If no grid point is selected, revert to default href
                return LINK_DEFAULT_HREF
        return LINK_DEFAULT_HREF
    else:
        return LINK_DEFAULT_HREF