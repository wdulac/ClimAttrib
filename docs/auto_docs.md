# Module `src/components/home/input_settings_top_bar.py`

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


---

# Module `src/components/home/location_selector.py`

# Module overview

This module provides the Leaflet-based location selector used on the home page.
It exposes a small Dash fragment containing an interactive map that renders a
vector grid (GeoJSON) of model grid cells, allows the user to zoom and select a
cell, and stores the selected coordinates in a dcc.Store for other UI
components to consume.

Primary features
- dl.Map configured with canvas renderer and custom max bounds / zoom limits.
- A GeoJSON layer (`geojson`) that receives tiled vector data (via a clientside
  fetch) and supports:
    - dynamic styling to highlight the selected cell,
    - client-side filtering to hide cells at low zoom levels,
    - click handling to pick a grid cell.
- A Store component (`input:selected-point`) that holds the JSON-serialized
  [lat, lon] coordinates of the currently selected grid cell.
- Small UI hint text (`zoom-to-select`) that is shown/hidden depending on zoom.

Integration & assets
- Client-side JS lives under assets/ and must provide the following functions:
  - clientside.updateGridTiles(bounds, hideout) -> fetch and return GeoJSON tiles
  - clientside.select_point(clickData, zoom, hideout) -> updated hideout + point
  - clientside.update_zoom(zoom, hideout) -> updated hideout with zoom level
  - A dashExtensions Namespace 'dashExtensions.geojson' must expose
    `colorCell` and `zoomFilter` used by the GeoJSON component.
- The helper JS `assets/js/leaflet_extras.js` is expected to contain the above
  helpers and must be present for full UX.

Callbacks (server-side)
- zoom_to_select(zoom, is_hidden):
    Toggle visibility of the "zoom to select" hint based on zoom level.
- clear_point_data(zoom, clickData):
    Clears previous clickData when zooming out to avoid reselecting cells.
- Several clientside callbacks wire the map bounds/zoom/clicks to GeoJSON data
  and to the stored selected point.

Component ids (important)
- 'map' (dl.Map)
- 'geojson' (dl.GeoJSON)
- 'marker' (dl.LayerGroup)
- 'zoom-to-select' (html.Div)
- 'input:selected-point' (dcc.Store)

Notes & recommendations
- The GeoJSON tiles fetched by the client are generally lightweight but the
  tile service must be accessible from the browser. Keep heavy work off the
  Dash server (use clientside JS).
- Use the dcc.Store `input:selected-point` as canonical source of truth for
  downstream callbacks; do not rely on GeoJSON.clickData directly.
- Keep the JS helpers in assets/ under version control; changes to their API
  must be reflected in this module and any other components that use them.

Usage
- Import and include `location_selector` in the app layout. Other components
  (e.g. input_settings_top_bar) expect `input:selected-point` to exist.

