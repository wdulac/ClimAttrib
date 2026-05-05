# Application architecture

## What the application does

WeatherAttrib is a web application that performs **climate event attribution**: given an observed extreme temperature event (a heatwave, a cold snap) defined by a location, a date range, and a measured intensity, it estimates how much more or less likely that event is to occur in today's climate compared to a pre-industrial baseline. The results include probability ratios, return periods, intensity shifts, and a confidence interval on each, presented as both charts and automatically generated explanatory text.

The application is designed for interactive, on-demand use: a scientist or analyst selects an event in the browser and receives results within ~20 seconds.

---

## The three runtime components

The application is built around the cooperation of three distinct processes that must all be running simultaneously.

### 1. The web server (Flask + Dash)

**Flask** is a Python web server framework: it listens for HTTP requests from the browser and serves responses (web pages, data, files). All browser communication goes through it.

**Dash** is a Python library that sits on top of Flask and provides a reactive interface model: the page is built from Python components (buttons, maps, charts), and Python callback functions are automatically triggered when the user interacts with those components. This avoids writing explicit JavaScript for most interactions.

Together, Flask and Dash serve the two pages of the application (home and analysis), handle user inputs, dispatch computation tasks, and assemble the results view once computation is complete.

The WSGI callable exposed to production servers (e.g. gunicorn) is the Flask `server` object in `src/app.py`.

### 2. The background worker (Celery)

The attribution calculation takes ~20 seconds and involves CPU-intensive scientific computation. Running it directly inside the web server would block the server from handling any other requests for the duration.

**Celery** is a task queue system: the web server places a computation request (a "task") into a queue, and a separate Celery worker process picks it up and executes it independently. The web server immediately returns control to the browser, which then polls for the result.

On a local development machine, celery worker(s) can be started via `./scripts/start_celery.sh`. The worker configuration is in `src/app_platform/compute/celery.py`.

### 3. Shared memory (Redis)

**Redis** is a fast in-memory data store. In this application it serves two distinct roles, separated into two database slots:

- **DB 0 — task queue**: used by Celery as the communication channel between the web server (which enqueues tasks) and the workers (which dequeue and execute them).
- **DB 1 — result cache**: once a worker finishes computing an attribution result, it serialises the result (as a Python object) and writes it to Redis DB 1 with a 48-hour expiry. The web server reads from this cache when displaying results, and also checks it first to avoid recomputing results that are already available.

On a local development machine, Redis can be started via `./scripts/start_redis.sh`. Redis is configured in `redis.conf`.

---

## Full user flow

```
Browser                     Web server (Flask/Dash)             Redis              Celery worker
  │                                  │                             │                      │
  │── open home page ───────────────►│                             │                      │
  │◄── map + input form ─────────────│                             │                      │
  │                                  │                             │                      │
  │── select location + dates ──────►│ (reads ERA5 NetCDF)         │                      │
  │◄── observed temp + anomaly ──────│                             │                      │
  │                                  │                             │                      │
  │── click "Continue" ─────────────►│ (encodes event as           │                      │
  │◄── redirect to /analysis?p=... ──│  a signed URL token)        │                      │
  │                                  │                             │                      │
  │── load /analysis?p=... ─────────►│ (decodes token)             │                      │
  │                                  │── check cache (DB 1) ──────►│                      │
  │                                  │◄── miss ────────────────────│                      │
  │                                  │── queue task (DB 0) ───────►│── dequeue ──────────►│
  │◄── loading screen ───────────────│                             │                      │
  │                                  │                             │       compute...     │
  │── poll every 1 s ───────────────►│── check cache (DB 1) ──────►│                      │
  │◄── not ready yet ────────────────│◄── miss ────────────────────│                      │
  │                                  │                             │◄── store result ─────│
  │── poll ─────────────────────────►│── check cache (DB 1) ──────►│                      │
  │                                  │◄── hit ─────────────────────│                      │
  │◄── results carousel ─────────────│                             │                      │
```

### Step 1 — Home page: event definition

The home page (`src/pages/home.py`) renders two main areas:
- An interactive map (Leaflet) where the user clicks a grid cell to select lat/lon coordinates.
- An input bar (`src/components/home/input_settings_top_bar.py`) with controls for event type (hot/cold), date range, and computation method (yearmax or calendar-restricted).

When the user selects a location and a valid date range, a Dash callback reads the corresponding daily ERA5 temperature from a NetCDF file on disk, computes the observed mean and its anomaly relative to the smoothed climatology, and displays the result in the input bar.

Once the inputs are complete, all event parameters are packed into a compact binary payload and signed with an HMAC (to detect any tampering) by `src/app_platform/shared/tokens.py`. This signed payload is base64-encoded into a URL token. Clicking "Continue" navigates to `/analysis?p=<token>`.

### Step 2 — Analysis page: dispatching the computation

The analysis page (`src/pages/analysis.py`) receives the token in the URL, decodes and verifies it, and reconstructs the event dictionary. It then computes a deterministic cache key from that dictionary (a SHA-256 hash of the JSON-sorted event parameters).

- **Cache hit**: the result is already in Redis DB 1. The page is rendered immediately with the full results carousel.
- **Cache miss**: a Celery task is queued (via Redis DB 0), and the page renders a loading skeleton. A timer fires every second, triggering a callback that checks Redis DB 1 until the result appears.

### Step 3 — Worker: computing the attribution

The Celery `attribution` task (`src/app_platform/compute/celery.py`) calls `attribute_event()` from `src/science/attribution/event_attribution.py`. The computation proceeds as follows:

1. **Load the prior distribution**: a pre-computed statistical model of local temperature extremes, read from a NetCDF file (`data/prior/`). The model is parametrised by a covariate (Global Mean Surface Temperature, GMST) and spans 1850–2100 under two climate scenarios.
2. **Load the observation timeseries**: annual extreme temperature values at the selected grid point, read from `data/Yo/`.
3. **Run the MCMC constraint**: using the ANKIALE library and Stan (a probabilistic programming language compiled to native code), the prior distribution is updated ("constrained") by the observations. This step is the computational bottleneck and is parallelised across multiple processes using `ProcessPoolExecutor`.
4. **Compute attribution metrics**: from the constrained distribution, the code derives probabilities of the event occurring in the factual world (with anthropogenic forcing) and in a counterfactual world (without). Derived quantities include the probability ratio (PR), fraction of attributable risk (FAR), return periods, and intensity shift (ΔI), each with confidence intervals.
5. **Store the result**: the result (an `xarray.Dataset`) is pickled and written to Redis DB 1 with a 48-hour TTL. The web server's polling callback then picks it up.

### Step 4 — Results display

Once the cache entry is found, the polling callback replaces the loading skeleton with a results carousel (`src/components/analysis/carousel.py`) containing four slides:

1. **Automated text** (`src/components/analysis/sentence_generator/`): a structured text generated from Jinja2 templates filled with formatted metric values. Three time horizons are covered: the event year, the current year, and 2050.
2. **Probability charts**: `pF` and `pC` time series (factual and counterfactual probabilities), and PR/FAR.
3. **Intensity charts**: `IF` and `IC` time series (factual and counterfactual intensities), and ΔI.
4. **Observations**: the historical Yo timeseries with estimated return levels, and the local annual cycle.

---

## Directory map

```
src/
├── app.py                      Entry point: Flask + Dash initialisation, route registration
├── app_platform/
│   ├── compute/
│   │   ├── celery.py           Celery application, attribution task definition
│   │   └── redis.py            Redis client wrapper (cache read/write/key generation)
│   ├── shared/
│   │   ├── config.py           Loads .env, exports all runtime settings
│   │   ├── paths.py            Project-relative path constants (DATA, SRC, ASSETS...)
│   │   ├── tokens.py           HMAC-signed URL token encode/decode
│   │   └── urls.py             URL prefix helpers
│   └── web/
│       ├── api/                Public HTTP routes (grid tiles, CSV download)
│       ├── admin/              Protected HTTP routes (cache clear, restart, Stan compile)
│       └── redirects.py        URL rewriting rules
├── pages/
│   ├── home.py                 Home page layout (assembles map + input bar)
│   └── analysis.py             Analysis page layout + polling callback
├── components/
│   ├── home/
│   │   ├── input_settings_top_bar.py   Event input UI + temperature readout callbacks
│   │   └── location_selector.py        Interactive map component + point selection callbacks
│   ├── analysis/
│   │   ├── carousel.py                 Results carousel (assembles all slides)
│   │   ├── __plotly_plots.py           Dash element builders for Plotly figures (called by carousel)
│   │   ├── event_description/          Banner above carousel (event summary + back button)
│   │   └── sentence_generator/         Automated text generation from attribution results
│   ├── layout/                 Header, footer, disclaimer (Common to all pages)
│   └── resources/              Markdown strings for tooltips and help text
├── science/
│   ├── attribution/            Core attribution algorithm (event_attribution.py + helpers)
│   └── visualisation/          Plotly figure builders for science plots (annual cycle, Yo)
└── formatting/                 Metric formatting functions (probability, return period, etc.)

data/                           Large NetCDF files (not versioned, assumed present on disk)
├── prior/                      Pre-computed constrained prior distributions (*_CONSTRAIN_X.nc)
├── Yo/                         Observed annual extreme timeseries
├── daily/                      ERA5 daily temperature (used for live intensity readout)
└── annual_cycle/               Smoothed daily climatology (used for anomaly display)
```

---

# Module `src/app.py`

Application entry point.

Creates the Flask server and the Dash application that sits on top of it, assembles
the top-level page layout (header, footer, disclaimer, page container), then registers
API routes, admin routes, and URL redirect rules on the Flask server.

The module-level ``server`` object (a Flask instance) is the WSGI callable used by
production servers (e.g. ``gunicorn --bind 0.0.0.0:8000 src.app:server``).
For development, run directly with ``python src/app.py`` (settings are read from
``.env`` via ``app_platform.shared.config``).

Import order matters: the ``app_platform.web`` modules must be imported after the
Flask ``server`` object is created, and ``register_disclaimer_callbacks`` must be
called before ``application.layout`` is assigned.


---

# Module `src/app_platform/`

Infrastructure layer: runtime services and cross-cutting utilities.

Sub-packages:

- ``compute/`` — Celery worker configuration and the ``attribution`` task; Redis
  cache client (DB 1).
- ``shared/`` — utilities that any module in the application can import: runtime
  settings (``config``), project-relative path constants (``paths``), HMAC-signed
  URL tokens (``tokens``), and URL prefix helpers (``urls``). Pages, Dash
  components, science modules, and workers all draw from this sub-package.
- ``web/`` — Flask Blueprint registrations for the public API routes and the
  password-protected admin routes.


---

# Module `src/app_platform/compute/celery.py`

Celery application and background task definitions.

Configures a Celery instance using Redis DB 0 as its task broker. Defines two tasks:

- ``attribution`` — the main computation task. Calls ``attribute_event()`` from
  ``science.attribution``, stores the result in the Redis cache (DB 1) under the
  event's cache key. Applies a 2-minute soft time limit and a 2.5-minute hard limit.
  On soft timeout, writes a ``{'status': 'timeout'}`` sentinel to the cache with a
  5-second TTL so the polling callback on the analysis page can detect and report
  the failure.

- ``compilation`` — compiles a Stan model (GEV or Normal) using the ANKIALE library.
  Dispatched by the admin ``/stan-compile`` endpoint; chained so both models compile
  sequentially on a single worker when both are missing.

The ``celery_app`` object is imported by ``pages/analysis.py`` to retrieve and queue
the ``attribution`` task.


---

# Module `src/app_platform/compute/redis.py`

Redis cache layer — DB 1.

Wraps a Redis client connected to DB 1 (separate from the Celery broker on DB 0) and
provides helpers for storing and retrieving attribution results.

Cache entries are pickled Python dicts with a ``'status'`` key (``'ok'`` or
``'timeout'``) and, for successful results, a ``'result'`` key containing an
``xarray.Dataset``.

Public API:

- ``make_cache_key(event)`` — SHA-256 of the JSON-sorted event dict; same event always
  produces the same key.
- ``set_cache(key, value, ttl)`` — pickle and store with expiry (default 48 h).
- ``get_cache(key)`` — retrieve, unpickle, and reset TTL; returns ``None`` if missing.
- ``cache_exists(*keys)`` — returns True only if all supplied keys are present.
- ``delete_cache(key)`` — remove a single entry.
- ``redis_client`` — the raw ``redis.Redis`` instance, used directly by admin routes.


---

# Module `src/app_platform/shared/config.py`

Runtime configuration loader.

Loads the ``.env`` file from the project root (via ``python-dotenv``) and exports
typed settings used across the application:

- ``APP_HOST``, ``APP_PORT``, ``APP_DEBUG`` — Flask/Dash server binding parameters.
- ``APP_SHOW_DASH_DEV_TOOLS`` — enables Dash's hot-reload overlay and debug panel.
- ``URL_PREFIX`` — URL path prefix for all routes (e.g. ``/eventtest``), empty string
  when the app is served at the root.
- ``URL_PREFIX_DASH`` — same prefix formatted for Dash's ``url_base_pathname``
  (always ends with ``/``).
- ``PRODUCTION`` — when True, enables the ProxyFix WSGI middleware in ``app.py``
  to correctly handle headers set by a reverse proxy.

This module must be imported early. Celery workers import it as their first import
so that ``.env`` variables are loaded before any other module reads ``os.getenv``.


---

# Module `src/app_platform/shared/paths.py`

Project-relative path constants.

Locates the project root by walking up the directory tree from this file until a
known marker file (``.git``, ``requirements.txt``, ``redis.conf``, ``.env``) is
found, then exposes the following ``pathlib.Path`` constants:

- ``ROOT`` — project root directory.
- ``SRC`` — ``ROOT/src``.
- ``DATA`` — ``ROOT/data`` (large NetCDF datasets, not versioned).
- ``ASSETS`` — ``SRC/assets``.
- ``COMPONENTS`` — ``SRC/components``.
- ``MARKDOWN_RESOURCES`` — ``COMPONENTS/resources/md`` (tooltip and help Markdown files).

Never hardcode filesystem paths anywhere in the codebase; always import from this module.


---

# Module `src/app_platform/shared/tokens.py`

HMAC-signed URL token encoding and decoding.

Packs an event's parameters (extreme type, computation method, start/stop dates,
lat, lon, intensity) into a compact 22-byte binary payload using ``struct``,
appends a 16-byte truncated HMAC-SHA256 signature, and encodes the result as a
URL-safe base64 string. The token is passed from the home page to the analysis page
as the ``p`` query parameter.

Public API:

- ``encode_token(extreme_type, computation_method, date, lat, lon, intensity) -> str``
- ``decode_token(token: str) -> dict`` — verifies the signature (raises ``ValueError``
  on mismatch) and returns an event dict that includes derived fields: ``date``
  (midpoint), ``duration`` (in days), and string-to-enum conversions for
  ``extreme_type`` and ``method``.

The signing key is read from the ``URL_SIG_SECRET_KEY`` environment variable. A
random key is generated at startup if the variable is absent (development fallback;
tokens will not survive server restarts in that mode).


---

# Module `src/app_platform/shared/urls.py`

URL helper functions.

Provides two small utilities that prepend the configured URL prefix
(from ``config.URL_PREFIX``) to relative paths:

- ``asset_url(path)`` — builds a URL pointing to a file under ``/assets/``.
- ``page_url(path)`` — builds a URL pointing to a page route.

Used when constructing ``src`` attributes for images and ``href`` attributes for
links that must remain correct whether the app is served at the root or at a
sub-path (e.g. ``/eventtest/``).


---

# Module `src/app_platform/web/`

Flask route registrations for the web layer.

- ``api/`` — public endpoints (GeoJSON tiles, CSV download); mounted under
  ``/api/``.
- ``admin/`` — protected endpoints (cache clear, process restart, Stan
  pre-compilation); mounted under ``/admin/``, all require a valid
  ``ADMIN_SECRET`` signature.
- ``redirects.py`` — URL rewriting rules applied at app startup.


---

# Module `src/app_platform/web/redirects.py`

URL redirect rules attached as a Flask ``before_request`` hook.

Validates incoming GET requests to ``/analysis`` before they reach Dash, redirecting
to the home page if:

- The ``p`` query parameter is absent.
- There is more than one query parameter.
- The base64-decoded payload is 16 bytes or shorter (a basic length check before the
  full HMAC verification done in ``pages/analysis.py``).

Registered on the Flask server by ``register_redirects(server)`` called from
``app.py``.


---

# Module `src/app_platform/web/api/`

Flask Blueprint for public API endpoints.

Routes serve map tile data (GeoJSON) and attribution results (CSV download).
The Blueprint is registered on the Flask app by ``register_api_routes`` defined
in ``src/app_platform/web/api/register.py`` and called from ``app.py``.


---

# Module `src/app_platform/web/api/register.py`

Registers the public API blueprint on the Flask server.

Importing ``geojson_tiles`` and ``download_csv`` has the side-effect of registering
their routes on ``api_bp``. The blueprint is then attached at ``{URL_PREFIX}/api``.
Flask-Compress is also configured here to gzip-compress API responses.

Called once from ``app.py`` during application startup.


---

# Module `src/app_platform/web/api/geojson_tiles.py`

HTTP endpoint: serve model grid cells as tiled GeoJSON.

Route: ``GET {URL_PREFIX}/api/grid_tiles``
Query parameter: ``bounds`` — JSON-encoded ``[[south, west], [north, east]]``
bounding box sent by the Leaflet map.

The model grid is pre-split into 10°×10° tile files stored under
``assets/static/grid_tiles/tile_{x}_{y}.geojson``. This endpoint selects the tiles
that overlap the requested bounding box, merges their features into a single GeoJSON
FeatureCollection, and returns the result. Individual tile files are cached in
memory with ``functools.lru_cache`` to avoid repeated disk reads.

Flask-Compress (enabled on the API blueprint by ``register.py``) gzip-compresses
the response automatically.


---

# Module `src/app_platform/web/api/download_csv.py`

HTTP endpoint: download attribution results as CSV.

Route: ``GET {URL_PREFIX}/api/download_csv``
Query parameters:

- ``key`` — Redis cache key identifying the desired result.
- ``variables`` — one of the variable group names: ``pF_pC``, ``PR``, ``IF_IC``,
  or ``dI``.

Retrieves the cached ``xarray.Dataset``, selects the requested variables, unstacks
the quantile dimension into separate columns (``<var>_QL``, ``<var>_BE``,
``<var>_QU``), prepends a human-readable comment header describing the variables,
and returns the result as a downloadable ``text/csv`` file.

Response codes: 400 if parameters are missing, 500 if the cache entry signals a
timeout or the dataset conversion fails.


---

# Module `src/app_platform/web/admin/`

Flask Blueprint for protected admin endpoints.

All routes defined here require a valid ``ADMIN_SECRET`` HMAC signature
(checked by ``__signature.py``). The Blueprint is registered on the Flask app
by ``register_admin_routes`` defined in
``src/app_platform/web/admin/register.py`` and called from ``app.py``.


---

# Module `src/app_platform/web/admin/register.py`

Registers the admin blueprint on the Flask server.

Importing ``clear_cache``, ``restart``, and ``stan_compile`` has the side-effect of
registering their routes on ``admin_bp``. The blueprint is then attached at
``{URL_PREFIX}/admin``.

Called once from ``app.py`` during application startup.


---

# Module `src/app_platform/web/admin/__signature.py`

HMAC signature verification for admin endpoints.

Admin requests must include two HTTP headers:

- ``Timestamp`` — Unix timestamp (seconds) of the request.
- ``Signature`` — HMAC-SHA256 hex digest of ``"{timestamp}:{route_name}"``, keyed
  with the ``ADMIN_SECRET`` environment variable.

``verify_signature(extra, timestamp, signature, max_age=30)`` returns True only if
the timestamp is within ``max_age`` seconds of now and the signature matches. The
route name (``extra``) is included in the signed payload to prevent a valid signature
for one endpoint from being replayed on another.


---

# Module `src/app_platform/web/admin/clear_cache.py`

Admin endpoint: clear the Redis result cache.

Route: ``POST {URL_PREFIX}/admin/clear-cache``
Required headers: ``Timestamp``, ``Signature`` (see ``__signature.py``).

Flushes all entries in Redis DB 1 (the attribution result cache). Does not affect
the Celery task queue in DB 0. Returns 403 if the signature is missing or invalid.


---

# Module `src/app_platform/web/admin/restart.py`

Admin endpoint: restart the application.

Route: ``POST {URL_PREFIX}/admin/restart``
Required headers: ``Timestamp``, ``Signature`` (see ``__signature.py``).

Performs a graceful restart in two steps:

1. Broadcasts a Celery ``shutdown`` control command to all workers.
2. Sends ``SIGHUP`` to the gunicorn master process, triggering a graceful worker
   reload without dropping in-flight requests.

Note that Redis doesn't need to be restarted as it is a standalone component.

Returns 403 if the signature is missing or invalid.


---

# Module `src/app_platform/web/admin/stan_compile.py`

Admin endpoint: pre-compile Stan statistical models.

Route: ``POST {URL_PREFIX}/admin/stan-compile``
Required headers: ``Timestamp``, ``Signature`` (see ``__signature.py``).

Checks which Stan model binaries (GEV, Normal) are absent from ``STAN_WORK_DIR``
and queues Celery ``compilation`` tasks for the missing ones. When both need
compiling, uses a Celery chain to run them sequentially on the same worker, avoiding
the memory spike of two simultaneous compilations. Returns 403 if the signature is
missing or invalid.

Stan models must be compiled before the ``attribution`` task can run. On a fresh
deployment, call this endpoint once before allowing user traffic.


---

# Module `src/pages/home.py`

Home page (route: ``/``).

Registers the Dash home page and defines its layout, composed of:

- ``event_definition_component()`` — the top input bar (date picker, event type,
  computation method, temperature readout, Continue button).
- ``interactive_map_component`` — the Leaflet map for grid cell selection.
- ``#home-plots-panel`` — a collapsible panel that shows contextual plots (annual
  cycle and Yo timeseries) once a location and valid date range are selected.

The layout function is called by Dash each time a user loads the page. All
interactive state is managed through callbacks defined in the component modules
(``components/home/``).


---

# Module `src/pages/analysis.py`

Analysis results page (route: ``/analysis``).

Receives the event token from the ``p`` URL query parameter, decodes and verifies it,
then renders the analysis layout in one of two modes:

**Cached result available**: retrieves the result from Redis DB 1 and renders the full
results carousel immediately. If the cached status is ``'timeout'`` (a previously
failed computation), deletes the entry and asks the user to reload.

**No cached result**: queues a Celery ``attribution`` task (expires if not started
within 5 minutes), renders a loading skeleton, and starts a ``dcc.Interval`` firing
every second. The ``update_results`` callback checks Redis on each tick; once the
cache entry appears it replaces the skeleton with the carousel and stops the interval.
After 300 ticks with no result, displays a saturation message.

The event description banner and Back button are always rendered immediately regardless
of loading state.


---

# Module `src/components/`

Dash UI components, organised by page.

- ``home/`` — components for the home page: the interactive map
  (``location_selector``) and the event parameter input bar
  (``input_settings_top_bar``).
- ``analysis/`` — components for the analysis page: the results carousel
  (``carousel``), the event description banner (``event_description``), and
  the automated text generator (``sentence_generator``).
- ``layout/`` — page-chrome components used on every page: header, footer,
  and the legal disclaimer modal.
- ``resources/`` — static text strings (Markdown tooltips, help text) shared
  across components.


---

# Module `src/components/home/`

Home-page components.

Exports:
- ``event_definition_component`` — top bar with event type, date, and intensity
  controls, plus the temperature readout.
- ``interactive_map_component`` — Leaflet map for grid-cell selection.


---

# Module `src/components/home/input_settings_top_bar.py`

Event definition bar — top of the home page.

Builds the input controls for specifying an extreme weather event and wires up the
Dash callbacks that keep those controls consistent.

## Layout

The bar contains:

- A date range picker (``input:date``) constrained to ``ALLOWED_DURATIONS`` (valid
  durations in days). A client-side JS function (``disableInvalidRange``, in
  ``assets/js/``) disables calendar dates that would produce an out-of-list duration.
- A segmented control for extreme type: ``hot`` / ``cold`` (``input:extreme-type``).
- A segmented control for computation method: ``yearmax`` (annual maximum, no
  seasonal restriction) or ``calendar`` (event compared only to the same period of
  the year) (``input:computation-method``).
- A temperature readout group showing the observed mean intensity, its anomaly
  relative to the 1991–2020 smoothed climatology, an anomaly direction icon, and
  the climatology 10th/50th/90th percentile range.
- A "Continue" button (``trigger:continue-btn``) wrapped in a link
  (``dynamic-link``). The link's ``href`` is updated with a signed URL token that
  encodes all current inputs; it falls back to the home page URL when inputs are
  incomplete.
- A ``dcc.Store`` (``data:intensity``) that persists the computed observed intensity
  value for other callbacks to consume.

## Callbacks

- ``update_disabled_dates`` — forwards the current date selection to the client-side
  ``disableInvalidRange`` function, which disables calendar dates that would create
  a duration not in ``ALLOWED_DURATIONS``.
- ``calendar_error`` — validates the selected date range and sets an error message
  on the picker when the duration is not in ``ALLOWED_DURATIONS``.
- ``update_temperature`` — reads the ERA5 daily file and the smoothed annual cycle
  NetCDF at the selected grid point and dates, computes the observed mean temperature
  and its anomaly. NetCDF values are in Kelvin; all displayed values are in °C.
- ``notify_user`` — shows a notification if the user clicks Continue without having
  first selected a grid point on the map.
- ``update_link`` — assembles a signed URL token from all valid inputs and sets it
  as the href of the Continue button link.

## Key component IDs

``input:date``, ``input:extreme-type``, ``input:computation-method``,
``input:selected-point`` (provided by ``location_selector``),
``temp-readout-value``, ``temp-readout-anomaly``, ``temp-readout-anomaly-icon``,
``temp-readout-clim``, ``data:intensity``, ``trigger:continue-btn``,
``dynamic-link``, ``notification-container``.


---

# Module `src/components/home/location_selector.py`

Interactive location selector — Leaflet map on the home page.

Renders a world map (``dl.Map``) with a GeoJSON overlay of model grid cells. The user
zooms in, clicks a cell to select a location, and the coordinates are stored in a
``dcc.Store`` for other components to consume.

## Layout

- ``dl.Map`` (id: ``map``) — Leaflet map with a fullscreen control, a base tile layer,
  and a ``LayerGroup`` for a selection marker.
- ``dl.GeoJSON`` (id: ``geojson``) — receives grid cell features fetched tile by tile
  from ``/api/grid_tiles`` as the user pans and zooms. Uses client-side JS functions
  to style the selected cell (``colorCell``) and hide all cells below the zoom
  threshold (``zoomFilter``). Both functions are in ``assets/js/leaflet_extras.js``.
- ``#zoom-to-select`` — a text hint shown when zoom level is below
  ``ZOOM_LEVEL_THRESHOLD`` (4).
- ``dcc.Store(id='input:selected-point')`` — canonical source of truth for the
  selected ``[lat, lon]`` pair; consumed by ``input_settings_top_bar`` callbacks.
- ``#home-plots-panel`` — a panel toggled by ``toggle_plots`` (in this module) that
  displays the annual cycle and Yo timeseries once a valid selection is made.

## Callbacks

Server-side:

- ``zoom_to_select`` — shows/hides the zoom hint based on current zoom level.
- ``clear_point_data`` — clears ``geojson.clickData`` when the user zooms out, to
  prevent the previous selection from being re-applied on the next zoom-in.
- ``toggle_plots`` — shows the contextual plots panel once a valid point and date
  range are both set.

Client-side (in ``assets/js/leaflet_extras.js``):

- ``clientside.updateGridTiles`` — fetches tile features from ``/api/grid_tiles`` for
  the current map bounds.
- ``clientside.select_point`` — updates the GeoJSON ``hideout`` (which drives cell
  highlighting) and writes the selected coordinates to ``input:selected-point``.
- ``clientside.update_zoom`` — keeps ``hideout.zoom`` in sync with the map zoom level,
  needed by the ``zoomFilter`` JS function.

## Key component IDs

``map``, ``geojson``, ``marker``, ``zoom-to-select``, ``input:selected-point``,
``home-plots-panel``.


---

# Module `src/components/analysis/`

Analysis-page components.

Exports:
- ``results_carousel`` — four-slide carousel: automated text, probability
  charts, intensity charts, observation plots.
- ``event_description_component`` — banner above the carousel summarising the
  event (location, dates, intensity, anomaly) with a back button.
- ``automated_text`` — human-readable attribution paragraph generated from
  Jinja2 templates.


---

# Module `src/components/analysis/carousel.py`

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
- ``carousel.blockSwiper`` — Prevents mouse drag from inside set containers from
  propagating back to the carousel, and therefore allows safe mouse interaction
  on text and plots without triggering a carousel swipe.


---

# Module `src/components/analysis/__plotly_plots.py`

Dash wrappers around the science visualisation figure builders.

Each function calls a figure builder from ``science.visualisation``, wraps the
resulting ``dcc.Graph`` in an ``html.Div`` with a pattern-matching id
(``{'type': 'plot-container', 'name': '...'}``), and returns the container.

The pattern-matching ids enable two client-side callbacks:

- ``carousel.blockSwiper`` — prevents the carousel's touch/drag from interfering
  with Plotly interactions inside a plot.
- ``plotly_extras.addButtonsToModebar`` — injects custom buttons ("Download CSV"
   and "Fullscreen") into each plot's toolbar.

Exported functions: ``probability_plot``, ``PR_FAR_plot``, ``intensity_plot``,
``intensity_change_plot``, ``observed_Yo_with_return_levels_plot``,
``annual_cycle_with_daily_obs_plot``.


---

# Module `src/components/analysis/event_description/`

Sub-package for the event description banner displayed above the results carousel.

Exports:
- ``event_description_component`` — the main banner component.

Internal modules:
- ``__event_key_figures`` — builds the row of summary cards (location, date
  range, observed intensity, computation method).
- ``__reverse_geocode`` — resolves lat/lon to a human-readable place name.
- ``__temperature_plot`` — legacy component, not used in the current flow.


---

# Module `src/components/analysis/event_description/analysis_description_component.py`

Event description banner component.

``event_description_component(event)`` returns a ``dmc.Paper`` panel containing
a row of key-figure cards summarising the event (location, date range, intensity,
method) and a "Back to event selection" button.

The back button is disabled while computation is in progress (driven by the
``is-loading`` store) and re-enabled once results are available.


---

# Module `src/components/analysis/event_description/__event_key_figures.py`

Key-figure cards for the event description banner.

``key_figures(event)`` builds a row of icon + label + value cards summarising
the event parameters: location with reverse-geocoded country/region, duration
and date range, observed intensity in °C, computation method, and (for the
calendar method) the centred ±1-week seasonal window computed from the event dates.


---

# Module `src/components/analysis/event_description/__reverse_geocode.py`

Grid-cell reverse geocoding using a Natural Earth shapefile.

Loads ``data/ne_10_admin/ne_10m_admin_1_states_provinces.shp`` at module import
time. ``reverse_lookup(lat, lon, cell_size)`` builds a bounding box centred on the
given coordinates, finds all administrative regions that intersect it, and returns
the one with the largest intersection area as a dict with keys ``'country'``,
``'region'``, and ``'sub-region'``. Returns ``None`` for ocean or uncovered cells.


---

# Module `src/components/analysis/event_description/__temperature_plot.py`

Legacy Matplotlib temperature sparkline (currently unused).

``make_temperature_plot(event)`` loads a hardcoded ERA5 NetCDF file (tx3d annual
maximum series), plots the timeseries as a small inline chart, and returns it as a
base64-encoded PNG data URI for use in an ``<img>`` src attribute. This module is
not referenced by the current carousel or event description components.


---

# Module `src/components/analysis/sentence_generator/`

Sub-package for generating the automated attribution text paragraph.

``automated_text(event, stats, lang)`` (from ``builder``) is the only public
entry point. The template selection logic and the structure of the template
context are documented in ``builder.py``.

Exports:

- ``automated_text`` — the fully automated textual attribution analysis.

Internal modules:

- ``__metrics`` — extracts raw numerical values (pF, pC, PR, FAR, dI, …) from
  the attribution ``xr.Dataset`` for the three time horizons (then/today/future).
- ``__phrases`` — turns those metrics into pre-formatted attribution phrases
  (e.g. "X [A to B] times more likely"), including IPCC bracket notation for
  confidence intervals.
- ``__data_models`` — dataclasses used to pass structured metric bundles between
  the modules above and the template.
- ``__loader`` — loads and caches the Jinja2 templates from
  ``sentence_generator/templates/``.
- ``__text_with_tooltip`` — earlier tooltip-based renderer, not used in the
  current flow.


---

# Module `src/components/analysis/sentence_generator/builder.py`

Automated text generator — public entry point of the sentence generator sub-module.

``automated_text(event, stats, lang)`` selects a Jinja2 template based on the nature
of the event, fills it with formatted metric values extracted from the attribution
result, and returns a ``html.Div`` containing the rendered Markdown text.

## Template selection

Templates live under ``sentence_generator/templates/en/``:

- ``extreme/{method}/{extreme_type}`` — used when ``pF < 80%`` (rare event) or the
  event intensity is within 1 K of the annual maximum.
- ``non_extreme/very_common`` — used when the event is common (``pF >= 80%``) and
  not close to the annual maximum.
- ``non_extreme/out_of_bound`` — used when ``pF == 1.0`` (the event is below the
  model's detection threshold).

## Template context

The template receives pre-formatted strings for three time horizons:

- **then** — the year of the event.
- **today** — the current year (omitted when the event happened in the current year).
- **future** — 2050.

For each horizon the context includes: probability (pF, pC), return periods (RP_F,
RP_C), intensity shift (dI), counterfactual intensity (IC), a PR/FAR attribution
phrase, and ratio phrases comparing consecutive horizons. All values include their
90% confidence interval formatted in IPCC bracket notation (e.g. ``4 [2 to 8] times``).


---

# Module `src/components/analysis/sentence_generator/__data_models.py`

Data classes for the sentence generator.

- ``CIValue(value, ql, qu)`` — a scalar metric together with its lower and upper
  confidence interval bounds (QL = 5th percentile, QU = 95th percentile).
- ``Metrics`` — a named collection of ``CIValue`` instances covering all attribution
  outputs for a single point in time: ``pF``, ``pC``, ``PR``, ``PR_inv``, ``FAR``,
  ``RP_F``, ``RP_C``, ``IF``, ``IC``, ``dI``.


---

# Module `src/components/analysis/sentence_generator/__metrics.py`

Metric extraction from the attribution xarray.Dataset.

``build_metrics(stats, t)`` selects all attribution variables at a given year ``t``
from the result ``xr.Dataset``, wraps each in a ``CIValue``, converts temperature
variables from Kelvin to °C, computes the inverse PR (used for "X times less likely"
phrasing), and returns a ``Metrics`` object ready for use in the template context.

Helpers: ``extract_ci(ds, var, t)`` extracts a single variable's three quantiles;
``invert_ci(ci)`` computes the reciprocal of a ``CIValue``, correctly swapping QL
and QU.


---

# Module `src/components/analysis/sentence_generator/__loader.py`

Jinja2 template loader for the sentence generator.

Initialises a Jinja2 ``Environment`` pointing at the ``templates/`` directory adjacent
to this file, with ``trim_blocks=True`` and ``lstrip_blocks=True`` for clean Markdown
output. The environment is cached by language with ``lru_cache``.

``render_template(name, variables, lang)`` loads ``templates/{lang}/{name}.tmpl`` and
renders it with the supplied context dict. Templates follow the Jinja2 syntax.


---

# Module `src/components/analysis/sentence_generator/__phrases.py`

Phrase-building functions for the sentence generator.

Assembles the natural-language fragments that cannot be expressed as static template
text because they depend on the sign of a metric:

- ``attribution_then``, ``attribution_today``, ``attribution_future`` — produce the
  PR/FAR attribution phrase for each time horizon. When ``PR >= 1`` the phrase reads
  "X times more likely" and includes the FAR; when ``PR < 1`` it reads "X times less
  likely" using the inverse PR, with no FAR.
- ``ratio_phrase(ratio, ratio_inv, fmt, past_tense)`` — produces the
  "increased/decreased by X" phrase comparing two consecutive time horizons.
- ``impossible_sentence(pC)`` — returns a caveat sentence if the lower confidence
  bound of the counterfactual probability reaches zero.
- ``event_definition_phrase(duration, To, extreme_type)`` — produces the event
  description opening (e.g. "having a two-day average temperature of 42.3 °C or higher").


---

# Module `src/components/analysis/sentence_generator/__text_with_tooltip.py`

Text renderer with inline confidence-interval tooltips (not used in the main flow).

``render_text_with_tooltips(paragraph)`` scans a string for ``[[CI:<label>|<display>]]``
tokens using a regex, replaces each token with a ``dmc.Tooltip`` that shows the full
confidence interval on hover, and returns a ``dmc.Text`` element mixing plain text
and tooltip elements.

This was an earlier design for displaying confidence intervals in the generated text.
The current implementation uses ``dcc.Markdown`` with CI values inlined as plain text
in IPCC bracket notation.


---

# Module `src/components/layout/`

Page-chrome components rendered on every page.

Exports:
- ``header`` — top navigation bar with logo and links.
- ``footer`` — bottom bar with credits and external links.
- ``disclaimer_layout`` — legal disclaimer modal (shown on first visit).
- ``register_disclaimer_callbacks`` — registers the open/close callbacks for
  the disclaimer modal.


---

# Module `src/components/layout/disclaimer.py`

Blocking disclaimer modal shown on first visit.

Exports ``disclaimer_layout`` (a list of Dash components: a ``dcc.Store`` and a
``dmc.Modal``) to be included in the top-level app layout, and
``register_disclaimer_callbacks(app)`` to be called after the Dash application
object is created (to avoid circular imports with ``app.py``).

The modal cannot be dismissed except by clicking "I understand". Acceptance is
persisted in the browser's local storage (``disclaimer-store``), so the modal is
only shown once per browser.


---

# Module `src/components/layout/header.py`

Application header component.

Exports a ``header`` element (``html.Header``) that spans the top of every page.
The left column contains the application title "WeatherAttrib" as a link to the home
page. The right column groups three modal-opening buttons — "How to use" (quick guide
and results interpretation tabs), "About" (project description and partner logos), and
"Disclaimer" — and a GitHub icon link.

Modals are opened and closed by a single pattern-matching callback (``toggle_modal``)
that matches on ``{"type": "modal-button", "name": MATCH}`` and
``{"type": "modal-content", "name": MATCH}``. Modal text content is loaded at import
time from Markdown files via ``components.resources``.


---

# Module `src/components/layout/footer.py`

Application footer component.

Exports a ``footer`` element (``html.Footer``) containing a copyright notice.
Included in the top-level layout in ``app.py``.


---

# Module `src/components/resources/text_resources.py`

Text resource loader — reads all Markdown files used by the UI at import time.

Exports the following string constants loaded from ``components/resources/md/``:

- ``QUICKGUIDE_CONTENT`` — quick-start guide shown in the header "How to use" modal.
- ``INTERPRETATION_HELP_CONTENT`` — results interpretation guide (second tab).
- ``DISCLAIMER_CONTENT`` — disclaimer text shown in the blocking modal and header button.
- ``ABOUT_CONTENT`` — project description shown in the "About" modal.
- ``COMPUTE_TOOLTIP_CONTENT`` — tooltip explaining the "Seasonal context" selector.
- ``ANOMALY_TOOLTIP_CONTENT`` — tooltip explaining the anomaly readout.
- ``CLIMATOLOGY_TOOLTIP_CONTENT`` — tooltip explaining the climatology readout.


---

# Module `src/science/`

Scientific computation modules.

- ``attribution/`` — the core attribution pipeline: loads priors and
  observations, runs the MCMC constraint (ANKIALE/Stan), and computes the full
  set of attribution metrics (pF, pC, PR, FAR, return periods, intensity
  shift).
- ``visualisation/`` — Plotly figure builders for the science slides of the
  results carousel (annual cycle, Yo timeseries, attribution time series).


---

# Module `src/science/attribution/event_attribution.py`

Core attribution algorithm.

``attribute_event(event, n_process, save_to_disk)`` runs the full attribution
pipeline for a single event and returns an ``xarray.Dataset`` of attribution
statistics. This function is called by the Celery ``attribution`` task in
``app_platform.compute.celery``.

## Pipeline

1. **Load prior** (``__data_loading._load_prior``) — reads the pre-computed
   constrained climatology for the selected variable (hot/cold, yearmax/calendar,
   duration) from a NetCDF file in ``data/prior/``. The prior encodes the statistical
   distribution of temperature extremes as a function of a covariate (GMST), with
   hyperparameters (``hpar``) and their covariance matrix (``hcov``) at each grid
   point.

2. **Load observations** (``__data_loading._load_obs``) — reads the annual extreme
   timeseries (Yo) for the selected grid point from ``data/Yo/``. If the event
   intensity sets a new record compared to the timeseries, the current year is
   appended before computing the bias.

3. **MCMC constraint** — using ANKIALE's ``constraint_var`` and Stan, samples the
   posterior distribution of the hyperparameters given the observations. The work is
   split across ``n_process`` subprocesses via ``ProcessPoolExecutor``; each process
   handles a subset of the covariate samples (``N_SAMPLES_COV``).

4. **Compute attribution metrics** — from the constrained hyperparameters, derives:
   factual (pF) and counterfactual (pC) probabilities, their ratio (PR), fraction of
   attributable risk (FAR), return periods (RF, RC), and intensity estimates (IF, IC,
   dI) for two climate scenarios (ssp370, ssp585) across the full 1850–2100 time axis.
   Confidence intervals are computed as the 5th–95th percentile range across MCMC
   samples.

5. **Return** — an ``xr.Dataset`` with dimensions ``(scenario, time, quantile)``
   keyed by variable name (pF, pC, PR, FAR, RF, RC, IF, IC, dI, plus the law
   parameters). Only the scenario defined in ``__settings.SCENARIO`` is returned to
   the caller.


---

# Module `src/science/attribution/__settings.py`

Scientific parameters for the attribution algorithm.

All constants here are module-level and imported with ``*`` by ``event_attribution.py``
and ``__data_loading.py``:

- ``N_SAMPLES_COV`` — number of covariate (GMST) samples drawn from the prior (100).
- ``SIZE_CHAIN`` — number of posterior samples per MCMC chain (100).
- ``METHOD_CONSTRAINT`` — dict specifying how the GMST covariate is used in the
  constraint (``{'GMST': 'full'}``).
- ``USE_STAN`` — whether to use the Stan MCMC backend (True) or a pure-Python
  fallback.
- ``MASTER_SEED`` — global random seed for reproducibility (from env var
  ``MASTER_SEED``, default 123456).
- ``STAN_WORK_DIR`` — directory where compiled Stan model binaries are cached.
- ``N_SAMPLES_ATTRIB`` — number of hyperparameter samples used for confidence
  interval estimation (1000).
- ``CI`` — half-width of the confidence interval (0.1 → 5th–95th percentile range).
- ``SCENARIO`` — climate scenario used for results returned to the user (``'ssp370'``).


---

# Module `src/science/attribution/__data_loading.py`

Data loading helpers for the attribution algorithm.

- ``_load_prior(extreme_type, computation_method, start_date, stop_date, duration)``
  — selects the correct NetCDF file from ``data/prior/{method}/`` based on the event
  parameters, loads it as an ANKIALE ``Climatology`` object, and returns a dict of
  arrays needed by ``attribute_event``: hyperparameters (``hpar``, ``hcov``),
  projection matrices (``projF``, ``projC``), a period smoother, the statistical law
  class (``cnslaw``), and metadata (``time``, ``bper``, ``side``).

- ``_load_obs(lat, lon, extreme_type, computation_method, start_date, stop_date, duration)``
  — reads the annual extreme temperature timeseries (Yo) for the given grid point from
  ``data/Yo/``, converts the time axis to integer years, and returns an
  ``xr.DataArray`` with dimension ``time`` (years).

Variable naming convention: ``tmx{N}d`` for hot N-day maxima, ``tmn{N}d`` for cold
N-day minima; a ``15w_{doy_start:03d}-{doy_end:03d}`` suffix is appended for the
calendar method to identify the comparison window.


---

# Module `src/science/attribution/__calendar_utils.py`

Calendar utilities for the attribution algorithm.

Handles the day-of-year (DOY) convention used throughout the science layer: DOY 60
is permanently reserved for February 29, so non-leap years skip DOY 60 and DOY 366
is valid for all years (it maps to December 31 in non-leap years after a shift).

- ``_datetime_to_doy(date)`` — converts a ``datetime`` to a DOY in [1, 366] using
  the leap-year convention above.
- ``_doy_to_datetime(doy, year)`` — inverse conversion; raises ``ValueError`` for
  DOY 60 in a non-leap year.
- ``_best_window_from_range(day_start, day_end, n_days, win_len, step)`` — given an
  event date range (as DOY values, possibly wrapping across year boundaries), finds
  the 15-day comparison window (aligned to a 5-day grid) that best centres the
  event. Returns the window as ``(start_doy, end_doy)``. Used to select the
  matching prior file for the calendar computation method.


---

# Module `src/science/visualisation/attribution_plots.py`

Plotly figure builders for the attribution results charts.

All four functions take an ``xr.Dataset`` (the attribution result) and a ``cache_key``
string (embedded in the figure metadata for the CSV download button), and return a
``go.Figure``.

- ``plot_probability(stats, cache_key)`` — time series of pF and pC (factual and
  counterfactual probability). The y-axis uses a non-linear link function (arctan of
  log) so that the full range from near-zero to near-one is visible. A secondary y-axis
  shows the equivalent return period.
- ``plot_PR_FAR(stats, cache_key)`` — time series of the probability ratio (PR) with
  a secondary y-axis showing the fraction of attributable risk (FAR). Also uses a
  non-linear link function.
- ``plot_intensity(stats, cache_key)`` — time series of IF and IC (factual and
  counterfactual intensity), in °C (converted from Kelvin in-place before plotting).
- ``plot_intensity_change(stats, cache_key)`` — time series of dI (change in intensity
  due to human influence), in °C.

All figures include a vertical line marking the event year, a shaded confidence
interval band (QL–QU), and a median line (BE). Figure dimensions follow a 16:11 aspect
ratio at 180 mm width.


---

# Module `src/science/visualisation/climatology_plots.py`

Plotly figure builders for the observational context charts.

- ``plot_observed_Yo(event, stats, cache_key)`` — annual extrema timeseries (Yo)
  at the selected grid point, with the user-selected event highlighted (red dot and
  crosshairs). When ``stats`` is provided, also draws non-stationary 2-year and
  10-year return levels computed from the attributed GEV or Gaussian distribution
  parameters.

- ``plot_annual_cycle(event)`` — daily temperature for the event year plotted against
  the 1991–2020 smoothed climatology (10th–90th percentile band and median). The
  user-selected event period is highlighted with a grey rectangle. For the southern
  hemisphere or cold events where the relevant season straddles the calendar year,
  the time axis is shifted by 6 months so the event period appears near the centre
  of the chart.

Both functions call ``_load_clim_data`` and ``_load_obs`` from ``__data_loading`` to
read ERA5 NetCDF files and handle the DOY coordinate system defined in
``__calendar_utils``.


---

# Module `src/science/visualisation/__customdata.py`

Plotly ``customdata`` array builders for hover text in attribution charts.

Each function extracts the relevant quantiles from the attribution dataset, formats
them using ``formatting.metrics`` functions (with IPCC bracket notation), and returns
a 2D NumPy array of shape ``(n_time, n_columns)`` suitable for Plotly's
``customdata`` parameter.

- ``customdata_prob(stats, var)`` — probability + return period (two columns).
- ``customdata_PR(stats, var)`` — probability ratio + FAR (two columns).
- ``customdata_intensity(stats, var)`` — temperature in °C (one column).
- ``customdata_intensity_change(stats, var)`` — signed temperature change in °C
  (one column).


---

# Module `src/science/visualisation/__plotly.py`

Low-level Plotly figure building utilities.

- ``create_attribution_plotly_graph(stats, variables, cache_key, ...)`` — the generic
  figure builder used by all four attribution charts. Draws a shaded confidence band
  (QL–QU) and a median line (BE) for each variable, adds a vertical line at the event
  year, and configures one or two y-axes. Accepts an optional ``transform_func``
  applied to all y-values and tick positions (used for the non-linear probability
  axis). Figure dimensions are fixed at a 16:11 aspect ratio. The ``cache_key`` and
  variable names are stored in ``fig.layout.meta`` so the CSV download button can
  identify which dataset to export.

- ``_clim_plots_base_layout(fig, ...)`` — applies a common layout (dimensions, axis
  styling, legend placement, hover mode) to the observational context figures
  (``climatology_plots``).


---

# Module `src/formatting/`

Human-readable formatting of attribution metrics.

Converts raw numerical values (probabilities, return periods, probability
ratios, FAR, temperatures) into display strings with appropriate precision,
threshold-based boundary notation (``< 0.01 %``, ``> 10 000 years``, …), and
unit labels.

Exports:
- ``UNITS`` — dict mapping variable names to their display unit strings.
- ``format_probability`` — probability → percentage string.
- ``format_return_period`` — return period → year string.
- ``format_probability_ratio`` — PR → ratio string.
- ``format_fraction_of_attributable_risk`` — FAR → percentage string.
- ``format_temperature`` — temperature value → string with unit.


---

# Module `src/formatting/metrics.py`

Metric formatting functions for chart labels and hover text.

Converts raw floating-point attribution metrics into human-readable strings with
consistent significant figures, boundary handling (soft min/max), and optional units.
All functions handle the edge cases 0, ∞, and NaN.

- ``format_probability(x)`` — probability in [0, 1] → percentage string.
  Soft bounds: values below ``PROB_SOFT_MIN`` show "< X", above ``PROB_SOFT_MAX``
  show "> X".
- ``format_return_period(x)`` — return period in [1, ∞] → year count string.
  Supports compact notation (e.g. "1.2k") and a soft max.
- ``format_probability_ratio(x)`` — probability ratio in [0, ∞] → dimensionless
  string with soft min and soft max.
- ``format_fraction_of_attributable_risk(x)`` — FAR in [0, 1] → percentage string.
  Uses more significant figures above 99% and a soft max at 99.9%.
- ``format_temperature(x)`` — temperature or temperature difference → °C string.
  Supports optional forced one-decimal format and signed notation for deltas.

Formatting thresholds and defaults are in ``__settings.py``. Low-level rounding and
string conversion utilities are in ``__numbers.py``.


---

# Module `src/formatting/units.py`

Unit string functions for formatted metric values.

Exports a ``UNITS`` dict that maps each formatter function from ``metrics.py`` to a
corresponding unit function. Each unit function takes the raw numeric value and
returns the appropriate unit string (handling singular/plural for counts and return
periods).

``UNITS`` is consumed by ``sentence_generator.builder`` and
``science.visualisation.__customdata`` to append the correct unit when building
IPCC-style bracket notation strings.


---

# Module `src/formatting/__numbers.py`

Low-level number formatting utilities used by ``metrics.py``.

- ``_round_to_n_sigfigs(x, n)`` — rounds ``x`` to ``n`` significant figures.
- ``_fmt_sig(x, sig, nan_str, inf_str, thousand_sep)`` — converts a number to a
  string with ``sig`` significant figures in plain decimal notation (no scientific
  notation), with optional thousand separator and NaN/∞ handling.
- ``_compact_notation(val, sig)`` — formats large numbers with SI-like suffixes
  (k, M, G) for display in compact chart labels.


---

# Module `src/formatting/__settings.py`

Default thresholds and parameters for the ``formatting`` module.

- ``DEFAULT_SIG`` — default number of significant figures (2).
- ``PROB_SOFT_MIN`` / ``PROB_SOFT_MAX`` — percentage bounds below/above which
  probability strings switch to "< X" / "> X" notation (0.01% and 99.9%).
- ``RET_SOFT_MAX`` — return period above which the string reads "> 10 000 years".
- ``DEFAULT_THOUSAND_SEP`` — thousand separator character for large numbers (",").
- ``PR_SOFT_MIN`` / ``PR_SOFT_MAX`` — ratio bounds for probability ratio formatting.
- ``FAR_SIG_THRESHOLD`` — FAR percentage above which an extra significant figure is
  used (99%).
- ``FAR_SIG_SECONDARY`` — number of sig figs used above the threshold (3).
- ``FAR_SOFT_MAX`` — FAR percentage above which the string reads "> 99.9%" (99.9%).
- ``FAR_NAN_STR`` — string used for NaN FAR values ("--").

