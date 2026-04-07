# For typing
import sys
import numpy as np
import xarray as xr
import plotly.graph_objects as go

from .__plotly import (
    create_attribution_plotly_graph,
)

from .__customdata import (
    customdata_prob,
    customdata_PR,
    customdata_intensity,
    customdata_intensity_change
)

EPSILON = 10*sys.float_info.epsilon

## Link functions for the custom y axis

def plink(x: float, e: float=2/3) -> float:
	y = np.arctan( np.log(x) ) / (np.pi / 2)
	return np.power(1 + y, e)


def PRlink(x: float, e:float=3) -> float:
	y = np.arctan(np.log(x)) / (np.pi / 2)
	return np.sign(y) * np.power(np.abs(y), e)


## Individual plot creation

def plot_probability(stats: xr.DataArray, cache_key: str) -> go.Figure:

    yticks = np.array([EPSILON,1e-6,1e-3,1e-2,1/40,1/10,0.25,0.5,1-EPSILON])
    yticklabelsL = ["0", "0,0001%", "0,1%", "1%", "2,5%", "10%", "25%", "50%", "100%"]
    yticklabelsR = ["∞", "1 000 000", "1000", "100", "40", "10", "4", "2", "1"]

    fig = create_attribution_plotly_graph(
        stats,
        variables=['pF', 'pC'],
        cache_key=cache_key,
        yaxis_conf=[
            {
                'title': "Probability",
                'tickvals': yticks,
                'ticktext': yticklabelsL,
                'range': [EPSILON, 1-EPSILON]
            },
            {
                'title': "Return period [years]",
                'overlaying': "y",
                'side': "right",
                'tickvals': yticks,
                'ticktext': yticklabelsR,
                'range': [EPSILON, 1-EPSILON]
            }
        ],
        labels=['With human influence', 'Without human influence'],
        transform_func=plink,
        customdata_func=customdata_prob,
        hovermode='x unified',
        hovertemplate=(
            "<b>Probability</b> : %{customdata[0]}<br>"
            "<b>Return period</b> : %{customdata[1]}<br>"
            "<extra></extra>"
        )
    )

    return fig


def plot_PR_FAR(stats: xr.Dataset, cache_key: str) -> go.Figure:
    
    yticks = np.array([EPSILON, 1e-3, 1e-2, 0.1, 0.2, 1, 5, 10, 100, 1000, 1/EPSILON])
    yticklabelsL = ["0", "1/1000", "1/100", "1/10", "1/5", "1", "5", "10", "100", "1000", "∞"]
    ytickslabelsR = ["", "", "", "", "", "0%", "80%", "90%", "99%", "99,99%", "100%"]

    fig = create_attribution_plotly_graph(
        stats,
        variables=['PR'],
        cache_key=cache_key,
        yaxis_conf=[
            {
                'title': 'Probability ratio',
                'tickvals': yticks,
                'ticktext': yticklabelsL,
                'range': [EPSILON, 1/EPSILON]
            },
            {
                'title': 'Fraction of attributable risk [%]',
                'tickvals': yticks,
                'ticktext': ytickslabelsR,
                'range': [EPSILON, 1/EPSILON],
                'overlaying': 'y',
                'side': 'right'
            }
        ],
        xaxis_domain=[0, 0.91],
        # colors=["204,85,0"], # Orange foncé
        colors=["0,128,128"], # Turquoise foncé
        customdata_func=customdata_PR,
        hovermode='x unified',
        hovertemplate=(
            "<b>Ratio</b> : %{customdata[0]}<br>"
            "<b>FAR</b> : %{customdata[1]}<br>"
            "<extra></extra>"
        ),
        transform_func=PRlink
    )

    return fig


def plot_intensity(stats: xr.Dataset, cache_key: str) -> go.Figure:

    # Note to self: If this somehow causes issues (e.g offset subtracted multiple times) 
    # the alternative would be to add an offset parameter to the :create_attribution_plotly_graph: function.
    stats['IF'] -= 273.15
    stats['IC'] -= 273.15

    fig = create_attribution_plotly_graph(
        stats,
        variables=['IF', 'IC'],
        cache_key=cache_key,
        yaxis_conf=[{
            'title': 'Event intensity [°C]'
        },
        {'side': 'right', 'tickvals': [], 'ticktext': []}],
        labels=[
            'With human influence',
            'Without human influence'
        ],
        customdata_func=customdata_intensity,
        hovermode='x unified',
        hovertemplate=(
            "%{customdata[0]}"
            "<extra></extra>"
        )
    )

    return fig


def plot_intensity_change(stats: xr.Dataset, cache_key: str) -> go.Figure:

    fig = create_attribution_plotly_graph(
        stats,
        variables=['dI'],
        cache_key=cache_key,
        yaxis_conf=[{
            'title': 'Change in intensity [°C]',
            'tickformat': '+'
        },
        {'side': 'right', 'tickvals': [], 'ticktext': []}],
        customdata_func=customdata_intensity_change,
        hovermode='x unified',
        hovertemplate=(
             "%{customdata[0]}"
             "<extra></extra>"
        ),
        colors=["204,85,0"]
    )

    return fig