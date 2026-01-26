import numpy as np
import xarray as xr
import calendar
import plotly.graph_objects as go

from .__plotly import _clim_plots_base_layout

from science.attribution.__calendar_utils import _datetime_to_doy
from science.attribution.__data_loading import _load_obs

from utils.paths import DATA


def _GEV_return_level(
    mu:xr.DataArray,
    sigma: xr.DataArray,
    ksi: xr.DataArray,
    p: float
) -> xr.DataArray:
    
    """
    Computes non-stationnary GEV return level for a given set of GEV parameters
    and a set probability

    :mu: Non-stationnary position parameter
    :sigma: Non-stationnary dispersion parameter
    :ksi: Stationnary (but expressed through time) shape parameter
    :p: Probability of the desired return level (0.5 := 2-year ; 0.1 := 10-year)
    """

    return mu + (sigma/ksi) * ((-np.log(1-p))**(-ksi) - 1)


def _load_clim_data(event: dict):

    ## Evaluate event's year
    a = event['start_date']
    b = event['stop_date']
    # Take year from the mid-point date
    year = (a + (b-a) / 2).year

    ## Read daily timeseries for this year and grid point
    daily = xr.open_dataset(DATA / 'daily/era5_sfc_tas_1p5deg.nc').\
        sel(
            time=slice(f"{year}-01-01", f"{year}-12-31"),
            lat=event['lat'], lon=event['lon'] % 360
        )['tas']
    daily -= 273.15

    ## Read reference climatology at grid point
    ref = xr.open_dataset(DATA / 'annual_cycle/ERA5_120x240_smoothed_daily_annual_cycle_1991-2020.nc').\
        sel(
            lat=event['lat'], lon=event['lon'] % 360
        )['tas']
    ref -= 273.15

    return daily, ref


# ==================================================================
#  Annual maxima + non-stationary return levels
# ==================================================================

def plot_annual_max_series(
    event: dict,
    stats: xr.Dataset | None = None,
    cache_key: str | None = None
) -> go.Figure:
    """
    Annual maxima time series with optional non-stationary GEV return levels
    """

    # ------------------------------------------------------------------
    # Event metadata
    # ------------------------------------------------------------------
    To = event["intensity"] - 273.15
    Xo = (event["start_date"] + (event["stop_date"] - event["start_date"]) / 2).year

    obs = _load_obs(
        event['lat'], event['lon'],
        event['extreme_type'], event['method'],
        event['start_date'], event['stop_date'],
        event['duration']
    )

    Yo = obs - 273.15
    time = Yo.time.values

    fig = go.Figure()

    # ------------------------------------------------------------------
    # Annual maxima series
    # ------------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=time,
            y=Yo.values,
            mode="lines+markers",
            name="Annual maximum",
            line=dict(color="black", width=1),
            marker=dict(size=6),
            opacity=0.4,
            # hovertemplate=annual_series_hover(),
        )
    )

    # ------------------------------------------------------------------
    # User-selected event
    # ------------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=[Xo],
            y=[To],
            mode="markers",
            marker=dict(size=10, color="red"),
            name=f"{event['duration']}-day mean temperature",
            # hovertemplate=annual_series_hover(event=True),
        )
    )

    ymin = float(np.nanmin(Yo.values))
    xmin = float(np.nanmin(time))

    fig.add_shape(
        type="line",
        x0=Xo, x1=Xo, y0=ymin, y1=To,
        line=dict(color="red", dash="dash")
    )
    fig.add_shape(
        type="line",
        x0=xmin, x1=Xo, y0=To, y1=To,
        line=dict(color="red", dash="dash")
    )

    # ------------------------------------------------------------------
    # Return levels (optional)
    # ------------------------------------------------------------------
    if stats is not None:
        sign = {"hot": 1, "cold": -1}[event["extreme_type"]]
        bias = stats["bias"] - 273.15

        for p, label, dash in [
            (0.5, "2-year return level", "dash"),
            (0.1, "10-year return level", "dot"),
        ]:
            rl = (
                sign
                * _GEV_return_level(
                    stats["locF"].sel(quantile="BE"),
                    stats["scaleF"].sel(quantile="BE"),
                    stats["shapeF"].sel(quantile="BE"),
                    p,
                )
                .sel(time=Yo.time)
                + bias
            )

            fig.add_trace(
                go.Scatter(
                    x=rl.time.values,
                    y=rl.values,
                    mode="lines",
                    line=dict(color="blue", dash=dash),
                    name=label,
                    # hovertemplate=annual_series_hover(return_level=True),
                )
            )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    _clim_plots_base_layout(
        fig,
        xaxis_title="Time",
        yaxis_title="Temperature [°C]",
        cache_key=cache_key,
    )

    return fig



# ==================================================================
#  Daily climatology + reference cycle
# ==================================================================

def plot_daily_climatology(
    event: dict,
    cache_key: str | None = None
) -> go.Figure:
    """
    Daily temperature series for selected year against 1991–2020 climatology
    """

    a = event["start_date"]
    b = event["stop_date"]
    year = (a + (b - a) / 2).year

    daily, ref = _load_clim_data(event)

    doy = daily.time.dt.dayofyear

    if not calendar.isleap(year):
        # En année non bissextile : on décale tous les jours à partir du 1er mars de +1
        # Ainsi, 1er mars (60 non-leap) devient 61, ce qui laisse un "trou" pour 60 (29/02).
        month = daily.time.dt.month
        doy366 = xr.where(month >= 3, doy + 1, doy)
    else:
        # En année bissextile : pas de décalage, 29/02 existe déjà (doy==60)
        doy366 = doy
    
    # Reindex daily timeseries
    daily_doy = (
        daily
        .assign_coords(dayofyear=doy366)
        .swap_dims({'time': 'dayofyear'})
        .reindex(dayofyear=np.arange(1, 367))        # crée le NaN au 60 si non-leap
    )

    X = daily_doy.dayofyear.values

    fig = go.Figure()

    # ------------------------------------------------------------------
    # Daily temperature (year)
    # ------------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=X,
            y=daily.values,
            mode="lines",
            line=dict(color="black", width=1),
            name=f"{year} daily temperature",
            # hovertemplate=daily_temperature_hover(),
        )
    )

    # ------------------------------------------------------------------
    # Reference climatology (10–90%)
    # ------------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=X,
            y=ref.sel(quantile="10%").values,
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=X,
            y=ref.sel(quantile="90%").values,
            fill="tonexty",
            fillcolor="rgba(255,0,0,0.25)",
            line=dict(width=0),
            name="1991–2020 10–90%",
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=X,
            y=ref.sel(quantile="50%").values,
            mode="lines",
            line=dict(color="red", width=2),
            name="1991–2020 median",
            # hovertemplate=daily_temperature_hover(ref=True),
        )
    )

    # ------------------------------------------------------------------
    # User-selected period
    # ------------------------------------------------------------------
    fig.add_vrect(
        x0=_datetime_to_doy(a),
        x1=_datetime_to_doy(b),
        fillcolor="gray",
        opacity=0.3,
        layer="below",
        line_width=0,
        name="User selected time range",
    )

    # ------------------------------------------------------------------
    # Axes
    # ------------------------------------------------------------------
    tickvals = [15, 45, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]
    ticktext = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    fig.update_xaxes(
        range=[1, 366],
        tickvals=tickvals,
        ticktext=ticktext,
        title="Day of year",
    )

    _clim_plots_base_layout(
        fig,
        yaxis_title="Temperature [°C]",
        cache_key=cache_key,
    )

    return fig