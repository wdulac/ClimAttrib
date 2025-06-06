import xarray as xr
import numpy as np
import sys

import plotly.graph_objects as go

CONFIDENCE_INTERVAL=0.05
EPSILON = 10*sys.float_info.epsilon

def plink(x: float, e: float=2/3) -> float:
	y = np.arctan( np.log(x) ) / (np.pi / 2)
	return np.power(1 + y, e)


def PRlink(x: float, e:float=3) -> float:
	y = np.arctan(np.log(x)) / (np.pi / 2)
	return np.sign(y) * np.power(np.abs(y), e)


def _safe_prob(value, fp=2, min_val=EPSILON, zero_str="0", unit="%"):

    fmt = f".{fp}f"

    def _format_prob(p, fmt=fmt):
        p *= 100
        if round(p, 2) == 100:
            return format(p, ".0f")
        else:
            return format(p, fmt)
        

    if np.isnan(value):
        return "NaN"
    elif 100*value <= min_val:
        return " ".join([zero_str, unit]) if unit else\
            zero_str
    elif 100*value < pow(10, -fp):
        return " ".join([f"< {pow(10, -fp)}", unit]) if unit else\
            f"< {pow(10, -fp)}"
    else:
        return " ".join([_format_prob(value), unit]) if unit else\
            _format_prob(value)


def _safe_ret(value, max_val=1/EPSILON, inf_str="infinity", unit="year"):

    def _format_years(value):
        if round(value, 1) == 1:
            return "1"
        elif value < 20: # Entre 0 et 20
            return f"{value:.1f}"
        elif value < 100: # Entre 20 et 100
            return f"{round(value)}"
        elif value < 1000: # Entre 100 et 1000
            return f"{round(value/5) * 5}"
        elif value < 1_000_000:
            return f"{value / 1_000:.1f}k"
        elif value < 1_000_000_000:
            return f"{value / 1_000_000:.1f}M"
        else:
            return f"{value / 1_000_000_000:.1f}G"
        
    if np.isnan(value):
        return "NaN"
    elif np.isinf(value) or value >= max_val:
        return inf_str
    else:
        return " ".join((_format_years(value), unit+"s" if round(value, 1)>1 else unit)) if unit else\
            _format_years(value)
    
        
def plot_probability(stats: xr.DataArray):

    # Ratio and figure size
    mm = 1. / 25.4
    ratio = 16 / 11
    width = 180 * mm * 110  # 96 dpi
    height = width / ratio

    colors_fill =  ['rgba(255,0,0,0.5)', 'rgba(0,0,255,0.5)']
    colors_line =  ['rgba(255,0,0,0.8)', 'rgba(0,0,255,0.8)']
    colors_hl_bg = ['rgba(255,0,0,0.3)', 'rgba(0,0,255,0.3)']

    yticks = np.array([EPSILON,1e-6,1e-3,1e-2,1/40,1/10,0.25,0.5,1-EPSILON])
    yticklabelsL = ["0", "0,0001%", "0,1%", "1%", "2,5%", "10%", "25%", "50%", "100%"]
    yticklabelsR = ["∞", "1 000 000", "1000", "100", "40", "10", "4", "2", "1"]

    names = ['pF', 'pC']
    trace_names = ['With human influence', 'Without human influence']

    fill_traces = []
    median_traces = []

    for i, (name, tn) in enumerate(zip(names, trace_names)):
        time = stats.time.values
        be = stats[name].sel(quantile='BE').values
        ql = stats[name].sel(quantile='QL').values
        qu = stats[name].sel(quantile='QU').values

        # Lower trace
        lower = go.Scatter(
            x=time,
            y=plink(ql),
            mode='lines',
            line=dict(width=0),
            fill=None,
            showlegend=False,
            hoverinfo='skip'
        )
        # Upper trace
        upper = go.Scatter(
            x=time,
            y=plink(qu),
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor=colors_fill[i],
            showlegend=False,
            hoverinfo='skip'
        )
        fill_traces.extend([lower, upper])

        # Best estimate's trace
        median = go.Scatter(
            x=time,
            y=plink(be),
            customdata=np.stack([
                [_safe_prob(p) for p in be],
                [_safe_prob(p) for p in ql],
                [_safe_prob(p) for p in qu],
                [_safe_ret(1/p) for p in be],
                [_safe_ret(1/p) for p in qu],
                [_safe_ret(1/p) for p in ql]
            ], axis=-1),
            mode='lines',
            line=dict(color=colors_line[i], width=2),
            name=tn,
            legendrank=1-i,
            hovertemplate=(
                "<b>Year</b> : %{x}<br>" +
                "<b>Probability</b> : %{customdata[0]} <i>[%{customdata[1]} to %{customdata[2]}]</i><br>" +
                "<b>Return period</b> : %{customdata[3]} <i>[%{customdata[4]} to %{customdata[5]}]</i><br>" +
                "<extra></extra>"
            ),
            hoverlabel={
                 'bgcolor': colors_hl_bg[i],
                 'bordercolor': 'black',
                 'font': {
                      'color': 'black'
                 }
            }
        )
        median_traces.append(median)

    # Adding traces to the figure in specific order so that best estimates
    # are on top
    fig = go.Figure()
    for trace in fill_traces:
        fig.add_trace(trace)
    for trace in median_traces:
        fig.add_trace(trace)

    # Adding invisible and minimal scatter trace to get a secondary axis
    fig.add_trace(go.Scatter(
        x=[min(time), max(time)],
        y=[min(be), max(be)],
        yaxis="y2",
        mode='markers',
        opacity=0,
        showlegend=False,
        hoverinfo='skip'
    ))

    # Formating figure and most importantly axes
    fig.update_layout(
        width=width,
        height=height,
        meta=dict(initial_width=width, initial_height=height),
        margin=dict(l=60, r=60, t=40, b=40),
        yaxis=dict(
            title="Probability",
            tickvals=plink(yticks),
            ticktext=yticklabelsL,
            range=[plink(EPSILON), plink(1-EPSILON)],
            showline=True,
            linecolor='black',
            gridcolor='lightgrey',
            tickfont=dict(size=14, color='black'),
            title_font=dict(size=16, color='black', family='Arial')
        ),
        yaxis2=dict(
            title="Return period [years]",
            overlaying='y',
            side='right',
            tickvals=plink(yticks),
            ticktext=yticklabelsR,
            showgrid=False,
            showline=True,
            range=[plink(EPSILON), plink(1-EPSILON)],
            linecolor='black',
            tickfont=dict(size=14, color='black'),
            title_font=dict(size=16, color='black', family='Arial')
        ),
        xaxis=dict(
            title="Time",
            range=[1850, 2100],
            ticks='outside',
            showline=True,
            linecolor='black',
            gridcolor='lightgrey',
            mirror=True,
            tickfont=dict(size=14, color='black'),
            title_font=dict(size=16, color='black', family='Arial')
        ),
        plot_bgcolor='white',
        legend=dict(
            font=dict(size=14),
            bgcolor='rgba(255,255,255,0)',
            y=0.95
        ),
        modebar_remove=['select', 'lasso2d']
    )

    return fig