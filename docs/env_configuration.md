# Environment configuration (`.env`)

## Purpose

The `.env` file at the project root is the primary mechanism for passing
configuration to the application on the production server, where environment
variables cannot be set interactively. It is loaded at startup by
`python-dotenv` (called in `src/app_platform/shared/config.py`).

Most variables are exposed to the rest of the application as typed constants
through `app_platform.shared.config` (imported as `from app_platform.shared.config
import ...`). A few variables are read directly with `os.getenv` in the module
that needs them; those are noted below.

> **Type conversion.** Bash (and `python-dotenv`) treats every value as a
> string. There is no native boolean type. Boolean variables in this project are
> read with `.upper() == 'TRUE'`, so the only accepted truthy value is `True`
> (case-insensitive). Any other string — including `1`, `yes`, `on` — is
> treated as `False`. When adding a new boolean variable, apply the same pattern
> in `config.py` rather than relying on dotenv to interpret it.

---

## Application variables

These are read by the application's own Python code.

### Server binding

| Variable | Default | Exposed as |
|---|---|---|
| `HOST` | `127.0.0.1` | `config.APP_HOST` |
| `PORT` | `8000` | `config.APP_PORT` (int) |
| `DEBUG` | `False` | `config.APP_DEBUG` (bool) |
| `SHOW_DASH_DEV_TOOLS` | `False` | `config.APP_SHOW_DASH_DEV_TOOLS` (bool) |

- **`HOST` / `PORT`** — address and port on which the Flask development server
  binds. Ignored in production (gunicorn sets its own bind address via command
  line).
- **`DEBUG`** — enables Flask/Dash debug mode (verbose error pages, auto-reload).
  Must be `False` in production.
- **`SHOW_DASH_DEV_TOOLS`** — enables Dash's hot-reload overlay and debug panel
  in the browser. Independent of `DEBUG`; must be `False` in production.

### URL routing

| Variable | Default | Exposed as |
|---|---|---|
| `URL_PREFIX` | *(empty)* | `config.URL_PREFIX`, `config.URL_PREFIX_DASH` |
| `PRODUCTION` | `False` | `config.PRODUCTION` (bool) |

- **`URL_PREFIX`** — path prefix under which the application is mounted on the
  server (e.g. `/eventtest`). Leave empty to serve at the root. `config.py`
  derives two variants: `URL_PREFIX` (e.g. `/eventtest`) and `URL_PREFIX_DASH`
  (always ends with `/`, required by Dash's `url_base_pathname`).
- **`PRODUCTION`** — when `True`, enables the `ProxyFix` WSGI middleware in
  `app.py` so that Flask correctly reads the client IP and protocol from headers
  set by the reverse proxy (nginx/Apache). Set to `True` on the production server.

### Redis

| Variable | Default | Read directly in |
|---|---|---|
| `REDIS_HOST` | `127.0.0.1` | `app_platform/compute/celery.py`, `app_platform/compute/redis.py` |
| `REDIS_PORT` | `6380` | same |

- **`REDIS_HOST` / `REDIS_PORT`** — address of the Redis instance used both as
  the Celery task broker (DB 0) and the result cache (DB 1). The default port
  `6380` (not the Redis default `6379`) matches `redis.conf` at the project root.
  Read directly via `os.getenv` in both modules rather than through `config.py`.

### Security

| Variable | Default | Read directly in |
|---|---|---|
| `URL_SIG_SECRET_KEY` | random (insecure) | `app_platform/shared/tokens.py` |
| `ADMIN_SECRET` | *(none — required)* | `app_platform/web/admin/__signature.py` |

- **`URL_SIG_SECRET_KEY`** — HMAC-SHA256 key used to sign the event URL token
  (`?p=<token>`). If absent, a random key is generated at startup, which means
  any previously shared link becomes invalid after a restart. Must be set in
  production.
- **`ADMIN_SECRET`** — secret used to authenticate requests to the protected
  admin endpoints (`/admin/clear_cache`, `/admin/restart`, `/admin/stan_compile`).
  **Required** — the application will crash at the first admin request if this
  variable is not set (no default).

### Scientific computation

| Variable | Default | Read directly in |
|---|---|---|
| `MCMC_N_WORKERS` | `2` | `app_platform/compute/celery.py` |
| `MASTER_SEED` | `123456` | `science/attribution/__settings.py` |

- **`MCMC_N_WORKERS`** — number of parallel subprocesses spawned by
  `ProcessPoolExecutor` inside the attribution task. Each process handles a
  subset of the MCMC covariate samples. Increasing it reduces wall-clock time
  proportionally up to `N_SAMPLES_COV` (currently 100). Note that each
  subprocess may itself use multiple threads (Stan), so watch for CPU
  oversubscription.
- **`MASTER_SEED`** — integer seed for the NumPy random generator that produces
  all Stan and MCMC seeds. Fixing it makes attribution results exactly
  reproducible across runs for the same event.

---

## Variables read by external tools

These variables are set in `.env` so that they propagate to the process
environment at startup, but they are not referenced by `os.getenv` anywhere in
the application's Python code. They are consumed by libraries or tools invoked
by the application.

| Variable | Consumed by |
|---|---|
| `CMDSTAN` | `cmdstanpy` — path to the CmdStan installation directory. Must point to a compiled CmdStan release (e.g. `~/.cmdstan/cmdstan-2.36.0`). If absent, `cmdstanpy` cannot find the Stan compiler and MCMC will fail. |
| `MPLBACKEND` | `matplotlib` — selects the rendering backend. Set to `Agg` (non-interactive, no display) to prevent crashes on headless servers where no graphical display is available. |
| `MPLCONFIGDIR` | `matplotlib` — directory where matplotlib writes its cache (font cache, style cache). On production servers running as `www-data`, the default cache location (`~/.config/matplotlib`) is not writable. Set this to a directory where `www-data` has write permission to avoid startup warnings or failures. |
| `ESMKFILE` | `xesmf` — path to the `esmf.mk` makefile fragment that describes the ESMF installation (library paths, binaries). Required at **runtime**: `xesmf` reads this file to locate the ESMF shared libraries and executables. Typically found inside a conda environment, e.g. `$CONDA_PREFIX/lib/esmf.mk`. If absent or incorrect, imports of `xesmf` (imported by ANKIALE) will fail. |
