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
