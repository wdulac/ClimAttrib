# Module `src/components/home/input_settings_top_bar.py`

Module overview
---------------
This module implements the top settings bar used to select extreme-event inputs
for the attribution application. It builds a small Dash/Dash-Mantine UI
containing controls for event type, date selection, computation method, a
temperature readout, and a primary "Continue" action. Several callbacks keep
the UI consistent, validate user inputs, compute a brief temperature summary
from on-disk NetCDF resources, and generate a signed navigation token.
Primary features
----------------
- UI components:
    - Segmented control to choose extreme type ("hot" / "cold").
    - Segmented control to choose computation method ("Restrict to same dates":
        calendar or yearmax).
    - Date range picker (dmc.DatePickerInput) with validation/enforced allowed
        durations and a JS hook to dynamically disable invalid ranges.
    - Temperature readout group showing observed intensity, anomaly,
        anomaly icon, and climatology quantiles.
    - Continue button wrapped in a dcc.Link whose href is updated by inputs.
    - dcc.Store component 'data:intensity' used to persist computed intensity.
- Static resources loaded at module import:
    - Several Markdown files (help/tooltips) read from RESOURCES.
    - Icons configured via DashIconify and local constants for arrow/minus icons.
- Constants:
    - ALLOWED_DURATIONS: list of valid time-window lengths in days (default:
        [1, 2, 3, 4]).
    - LINK_DEFAULT_HREF: fallback URL used when inputs are incomplete.
Callbacks (behavior summary)
---------------------------
1) update_disabled_dates(date_range)
     - Output: 'input:date'.disabledDates
     - Purpose: When the user selects a date range, returns a structure with a
         "function" key ("disableInvalidRange") and options describing allowed
         durations and the current start/end. This leverages DMC's feature to
         disable invalid end/start dates on the client side.
     - prevent_initial_call=True.
2) calendar_error(dates: list) -> str
     - Output: 'input:date'.error
     - Purpose: Validate date selections and return human-friendly error
         messages. Handles partial selections (e.g. [start, None]) and empty-range
         edge cases. Enforces ALLOWED_DURATIONS and returns the appropriate error
         message or empty string on success.
3) update_temperature(grid_point, extreme_type, date, date_error)
     - Outputs:
         - 'temp-readout-value'.children (observed mean temperature string in °C)
         - 'temp-readout-anomaly'.children (anomaly string in °C)
         - 'temp-readout-anomaly-icon'.children (icon: up / down / minus)
         - 'temp-readout-clim'.children (climatology quantiles string in °C)
         - 'data:intensity'.data (numeric intensity stored as serialized string)
     - Purpose: Given a selected grid point and validated date range, opens two
         NetCDF datasets (observations and smoothed daily climatology) using
         xarray, computes the mean observed temperature over the selected dates,
         looks up the corresponding climatological quantiles by day-of-year,
         computes the anomaly (observed - median), and returns formatted UI
         strings and a stored intensity value.
     - Units and thresholds:
         - Input NetCDF values are in Kelvin; displayed values are converted to
             °C by subtracting 273.15.
         - Anomaly thresholds for icons: >= +0.5 (up arrow), <= -0.5 (down arrow),
             otherwise neutral (minus icon).
     - Notes:
         - This callback opens NetCDF files on disk (DATA/daily/era5_sfc_tas_1p5deg.nc
             and DATA/annual_cycle/..._smoothed_daily_annual_cycle_1991-2020.nc),
             so it may be I/O and memory intensive. Proper caching or lazy-loading
             strategies can be considered for production deployment.
         - The helper function _datetime_to_doy is used to map dates to day-of-year
             indices expected by the climatology dataset.
4) notify_user(n_clicks, selected_point_data)
     - Output: 'notification-container'.sendNotifications
     - Purpose: When the Continue button is clicked without a selected grid
         point, emit a notification instructing the user to choose a point.
     - If a point is present, the callback raises PreventUpdate (no notification).
5) update_link(grid_point, extreme_type, computation_method, date, date_error, intensity)
     - Output: 'dynamic-link'.href
     - Purpose: Compose a signed URL token (via utils.url_token.encode_token)
         encoding the input settings (extreme type, computation method, date range,
         lat/lon, intensity) and set the Continue button's href to navigate to the
         analysis page (/analysis?p=<token>).
     - Validation: Returns the default fallback href if the date is invalid, if
         the grid point is missing, or other required inputs are not ready.
Important component ids and stores
---------------------------------
- 'input:extreme-type' (SegmentedControl)
- 'input:computation-method' (SegmentedControl)
- 'input:date' (dmc.DatePickerInput)
- 'input:selected-point' (expected elsewhere in the app; a JSON-serialized
    [lat, lon] pair)
- 'temp-readout-value', 'temp-readout-anomaly', 'temp-readout-anomaly-icon',
    'temp-readout-clim' (UI elements in the temperature readout group)
- 'data:intensity' (dcc.Store used to persist computed intensity)
- 'trigger:continue-btn' (Button nested inside 'dynamic-link')
- 'dynamic-link' (Link wrapping the Continue button)
- 'notification-container' (component that accepts sendNotifications payloads)
Dependencies and side effects
----------------------------
- Relies on dash, dash_mantine_components, dash_iconify, dcc, html, xarray,
    and local utilities utils.url_token and utils.paths.
- Reads textual tooltip Markdown files from RESOURCES at import time.
- Reads NetCDF datasets from DATA within the update_temperature callback.
- Uses a small JS-side DatePicker helper ("disableInvalidRange") through DMC's
    disabledDates mechanism; that client-side function must be available for
    full UX enforcement of allowed durations.
Usage
-----
Import the module and include the exported layout fragment (input_settings_top_bar)
into the Dash application layout. The callbacks assume certain other app-level
components exist (in particular 'input:selected-point' and 'notification-container').
Ensure the DATA and RESOURCES paths resolve to the expected NetCDF and
Markdown files, and that encode_token is available to sign navigation tokens.
Error handling
--------------
- Callbacks return user-visible validation strings where appropriate and use
    PreventUpdate to avoid unnecessary updates.
- update_temperature wraps climatology quantile extraction in a try/except
    and falls back to NaNs if quantiles cannot be read for the selected
    coordinates/days.
Extensibility notes
-------------------
- ALLOWED_DURATIONS is a module-level constant and can be adjusted without
    changing callback logic; ensure client-side "disableInvalidRange" logic is
    kept in sync with this list.
- For production, consider caching opened datasets or using lazy/delayed
    loading to reduce per-callback I/O. Also validate and securely handle the
    encode_token inputs if exposed externally.

