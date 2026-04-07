import numpy as np

from formatting import UNITS
from formatting.metrics import (
    format_probability,
    format_return_period,
    format_probability_ratio,
    format_fraction_of_attributable_risk,
    format_temperature
)

def ipcc_custom_data(value, ql, qu, formatter, **kwargs):
    val = formatter(value, **kwargs)
    low = formatter(ql, **kwargs)
    high = formatter(qu, **kwargs)

    unit_func = UNITS.get(formatter)

    if unit_func:
        unit = unit_func(value)
        return f"{val} [{low} to {high}] {unit}"
    else:
        return f"{val} [{low} to {high}]"
    

def customdata_prob(stats, var):

    p = stats[var]

    rp_map = {
        "pF": "RF",
        "pC": "RC"
    }
    rp = stats[rp_map[var]]

    ql_p = p.sel(quantile="QL").values
    be_p = p.sel(quantile="BE").values
    qu_p = p.sel(quantile="QU").values

    ql_rp = rp.sel(quantile="QL").values
    be_rp = rp.sel(quantile="BE").values
    qu_rp = rp.sel(quantile="QU").values

    n = len(be_p)
    customdata = np.empty((n, 2), dtype=object)

    for i in range(n):
        customdata[i, 0] = ipcc_custom_data(
            be_p[i], ql_p[i], qu_p[i],
            format_probability
        )
        customdata[i, 1] = ipcc_custom_data(
            be_rp[i], ql_rp[i], qu_rp[i],
            format_return_period
        )

    return customdata


def customdata_PR(stats, var):

    pr = stats["PR"]
    far = stats["FAR"]

    ql_pr = pr.sel(quantile="QL").values
    be_pr = pr.sel(quantile="BE").values
    qu_pr = pr.sel(quantile="QU").values

    ql_far = far.sel(quantile="QL").values
    be_far = far.sel(quantile="BE").values
    qu_far = far.sel(quantile="QU").values

    n = len(be_pr)
    customdata = np.empty((n, 2), dtype=object)

    for i in range(n):
        customdata[i, 0] = ipcc_custom_data(
            be_pr[i], ql_pr[i], qu_pr[i],
            format_probability_ratio
        )
        customdata[i, 1] = ipcc_custom_data(
            be_far[i], ql_far[i], qu_far[i],
            format_fraction_of_attributable_risk
        )

    return customdata


def customdata_intensity(stats, var):

    da = stats[var]

    ql = da.sel(quantile="QL").values
    be = da.sel(quantile="BE").values
    qu = da.sel(quantile="QU").values

    n = len(be)
    customdata = np.empty((n, 1), dtype=object)

    for i in range(n):
        customdata[i, 0] = ipcc_custom_data(
            be[i], ql[i], qu[i],
            format_temperature,
            force_one_decimal=True
        )

    return customdata


def customdata_intensity_change(stats, var):

    da = stats[var]

    ql = da.sel(quantile="QL").values
    be = da.sel(quantile="BE").values
    qu = da.sel(quantile="QU").values

    n = len(be)
    customdata = np.empty((n, 1), dtype=object)

    for i in range(n):
        customdata[i, 0] = ipcc_custom_data(
            be[i], ql[i], qu[i],
            format_temperature,
            signed_notation=True,
            force_one_decimal=True
        )

    return customdata

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
### Dynamic hover templates for both Yo timeseries + annual cycle plots

def _annual_series_hover(event=False, return_level=False, p=None):
    if event:
        return (
            "<b>User event</b>: %{y:.1f} °C"
            "<extra></extra>"
        )

    if return_level:
        if p:
            pre = int(1/p)
            return (
                f"<b>{pre}-year return level</b>: %{{y:.1f}} °C"
                "<extra></extra>"
            )
        else:
            return (
                "<b>Return level</b>: %{y:.1f} °C"
                "<extra></extra>"
            )


    return (
        "<b>Annual maximum</b>: %{y:.1f} °C"
        "<extra></extra>"
    )


def _daily_temperature_hover(ref=False, year=None):

    if ref:
        return (
            "<b>1991 — 2020 median</b>: %{y:.1f} °C"
            "<extra></extra>"
        )
    else:
        return (
            "%{customdata}<br>"
            f"<b>Temperature</b>: %{{y:.1f}} °C"
            "<extra></extra>"
        )