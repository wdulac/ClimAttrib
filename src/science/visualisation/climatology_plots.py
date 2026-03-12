import numpy as np
import xarray as xr
from scipy.stats import norm
import calendar
import datetime as dt
import plotly.graph_objects as go

from .__plotly import _clim_plots_base_layout
from .__formatters import (
    _annual_series_hover,
    _daily_temperature_hover
)

from science.attribution.__calendar_utils import (
    _datetime_to_doy,
    _doy_to_datetime
)
from science.attribution.__data_loading import _load_obs

from app_platform.shared.paths import DATA


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


def _Gaussian_return_level(
    mu: xr.DataArray,
    sigma: xr.DataArray,
    p: float,
) -> xr.DataArray:
    """
    Computes (possibly non-stationary) Gaussian return level
    for exceedance probability p.
    
    p = 0.5  -> 2-year
    p = 0.1  -> 10-year
    """

    return mu + sigma * norm.ppf(1 - p)


def _return_level(
    stats: dict,
    p: float,
    method: str,
) -> xr.DataArray:

    if method == "yearmax":
        return _GEV_return_level(
            stats["locF"].sel(quantile="BE"),
            stats["scaleF"].sel(quantile="BE"),
            stats["shapeF"].sel(quantile="BE"),
            p,
        )

    elif method == "calendar":
        return _Gaussian_return_level(
            stats["locF"].sel(quantile="BE"),
            stats["scaleF"].sel(quantile="BE"),
            p,
        )

    else:
        raise ValueError(f"Unknown computation_method: {method}")
    

def _eval_shift(event: dict) -> int:

    shift = 0

    if event['extreme_type'] == 'hot' and event['lat'] < 0 : # Max annuel + hémis sud
        shift = 180
    
    elif event['extreme_type'] == 'cold' and event['lat'] > 0 : # Min annuel et hémis nord
        shift = 180

    return shift


def _load_clim_data(event: dict):

    ## Evaluate event's year
    a = event['start_date']
    b = event["stop_date"]
    t = (a + (b - a) / 2)
    shift_days = _eval_shift(event)

    if shift_days != 0:
        year = t.year if t.month >= 7 else t.year - 1
        t0 = dt.datetime(year, 7, 1)
        t1 = dt.datetime(year + 1, 6, 30)
    else:
        year = t.year
        t0 = dt.datetime(year, 1, 1)
        t1 = dt.datetime(year, 12, 31)

    ## Read daily timeseries for this year and grid point

    daily = xr.open_dataset(DATA / 'daily/era5_sfc_daily_tas.nc').\
        sel(
            time=slice(t0.isoformat(), t1.isoformat()),
            lat=event['lat'], lon=event['lon'] % 360
        )['tas']
    daily -= 273.15

    ## Read reference climatology at grid point
    ref = xr.open_dataset(DATA / 'annual_cycle/ERA5_120x240_smoothed_daily_annual_cycle_1991-2020.nc').\
        sel(
            lat=event['lat'], lon=event['lon'] % 360
        )['tas']
    ref -= 273.15

    if shift_days != 0:
        ref = ref.roll(dayofyear=shift_days)

    return daily, ref


# ==================================================================
#  Annual maxima + non-stationary return levels
# ==================================================================

def plot_observed_Yo(
    event: dict,
    stats: xr.Dataset | None = None,
    cache_key: str | None = None,
    **kwargs
) -> go.Figure:
    """
    Annual maxima time series with optional non-stationary GEV return levels
    """

    # Event metadata
    # ------------------------------------------------------------------
    To = event["intensity"] - 273.15

    a = event['start_date']
    b = event["stop_date"]
    t = (a + (b - a) / 2)

    shift_days = _eval_shift(event) # 0 or 180 days
    
    if shift_days != 0:
        year = t.year if t.month >= 7 else t.year - 1
    else:
        year = t.year

    Xo = year

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
    # D'abord les lignes horizontales qui repèrent le point sélectionné par l'utilisateur
    # ------------------------------------------------------------------
    
    # Ligne verticale : du bas de l'axe jusqu'au point sélectionné
    fig.add_shape(
        type="line",
        x0=Xo,
        x1=Xo,
        y0=0,
        y1=1,
        line=dict(color="red", dash="dash", width=1),
        xref="x",
        yref="paper"
    )
    
    # Ligne horizontale : du bord gauche de la figure jusqu'au point sélectionné
    fig.add_shape(
        type="line",
        x0=0,  # bord gauche de la figure
        x1=1,
        y0=To,
        y1=To,
        line=dict(color="red", dash="dash", width=1),
        xref="paper",
        yref="y"
    )

    # ------------------------------------------------------------------
    # Annual maxima series
    # ------------------------------------------------------------------

    extremum = {'hot': 'maxima', 'cold': 'minima'}[event['extreme_type']]

    fig.add_trace(
        go.Scatter(
            x=time,
            y=Yo.values,
            mode="markers",
            name=f"{event['duration']}-day {extremum}",
            marker=dict(color='black', size=6),
            opacity=1,
            hovertemplate=_annual_series_hover(),
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
            name="User selected event",
            hovertemplate=_annual_series_hover(event=True),
        )
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
                * _return_level(
                    stats,
                    p=p,
                    method=event['method']
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
                    hovertemplate=_annual_series_hover(return_level=True, p=p),
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
        **kwargs
    )

    return fig



# ==================================================================
#  Daily climatology + reference cycle
# ==================================================================

def plot_annual_cycle(
    event: dict,
    **kwargs
) -> go.Figure:
    """
    Daily temperature series for selected year against 1991–2020 climatology
    """

    a = event["start_date"]
    b = event["stop_date"]
    t = (a + (b - a) / 2)

    shift_days = _eval_shift(event) # 0 or 180 days

    if shift_days != 0:
        year = t.year if t.month >= 7 else t.year - 1
    else:
        year = t.year

    daily, ref = _load_clim_data(event)
    doy = daily.time.dt.dayofyear
    if shift_days != 0:
        doy = ((doy + 182 - 1) % 366) + 1

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

    base_year = 2000  # Année de référence bissextile
    
    dates_x = [_doy_to_datetime(d, base_year) for d in X]

    fig = go.Figure()


    # ------------------------------------------------------------------
    # Reference climatology (10–90%)
    # ------------------------------------------------------------------
    
    fig.add_trace(
        go.Scatter(
            x=np.array(dates_x),
            y=ref.sel(quantile="10%"),
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=np.array(dates_x),
            y=ref.sel(quantile="90%"),
            fill="tonexty",
            fillcolor="rgba(255,0,0,0.15)",
            line=dict(width=0),
            name="1991–2020 10–90%",
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=dates_x,
            y=ref.sel(quantile="50%").values,
            mode="lines",
            line=dict(color="red", width=2),
            name="1991–2020 median",
            hovertemplate=_daily_temperature_hover(ref=True),
        )
    )

    # ------------------------------------------------------------------
    # Daily temperature (year)
    # ------------------------------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=dates_x,
            y=daily_doy.values,
            customdata=daily.time.dt.strftime("%B %d, %Y"),
            mode="lines",
            line=dict(color="black", width=1.5),
            name=f"{year} daily temperature",
            hovertemplate=_daily_temperature_hover(year=year),
        )
    )


    # ------------------------------------------------------------------
    # User-selected period
    # ------------------------------------------------------------------

    doy_a = _datetime_to_doy(a)
    doy_b = _datetime_to_doy(b)
    
    if shift_days != 0:
        doy_a = ((doy_a + 182 - 1) % 366) + 1
        doy_b = ((doy_b + 182 - 1) % 366) + 1
    
    x0 = _doy_to_datetime(doy_a, base_year) - dt.timedelta(hours=12)
    x1 = _doy_to_datetime(doy_b, base_year) + dt.timedelta(hours=12)
    
    fig.add_vrect(
        x0=x0,
        x1=x1,
        fillcolor="gray",
        opacity=0.3,
        layer="below",
        line_width=0,
    )

    # ------------------------------------------------------------------
    # Axes
    # ------------------------------------------------------------------

    month_starts = [
    dt.datetime(base_year, m, 1)
    for m in range(1, 13)
    ] + [dt.datetime(base_year, 12, 31)]
    
    fig.update_xaxes(
        type="date",
        tickvals=month_starts,
        ticktext=[""] * len(month_starts),
        showticklabels=True,
        hoverformat="%B %d",
    )

    annotations = []
    
    months = list(calendar.month_abbr)[1:]
    if shift_days != 0:
        months = months[6:] + months[:6]
    
    for m in range(1, 13):
        start = dt.datetime(base_year, m, 1)
        end = dt.datetime(
            base_year, m, calendar.monthrange(base_year, m)[1]
        )
        mid = start + (end - start) / 2
    
        annotations.append(
            dict(
                x=mid,
                y=0,
                xref="x",
                yref="paper",
                text=months[m-1],
                showarrow=False,
                yshift=-30,
                font=dict(size=14),
            )
        )
    
    fig.update_layout(annotations=annotations)

    _clim_plots_base_layout(
        fig,
        xaxis_title="Time of year",
        yaxis_title="Temperature [°C]",
        extra_bottom_margin=27,
        standoff=30,
        **kwargs
    )

    return fig