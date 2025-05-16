import xarray as xr
import numpy as np

import plotly.graph_objects as go

CONFIDENCE_INTERVAL=0.05

def plink(x: float, e: float=2/3) -> float:
	y = np.arctan( np.log(x) ) / (np.pi / 2)
	return np.power(1 + y, e)


def PRlink(x: float, e:float=3) -> float:
	y = np.arctan(np.log(x)) / (np.pi / 2)
	return np.sign(y) * np.power(np.abs(y), e)


def _safe_str(value, fp=2, max_T_val=1e6, min_p_val=1e-12,
              inf_str="infinity", zero_str="0", unit=""):
    """
    Replaces probablities / return values by strings that are safe to
    display in plotly's hover label.

    Limits how small or how large values can be displayed.
    Handles infinite confidence interval.

    :value: Either a probability in [0, 1] or a return period in [1, ∞]
    :fp: Desired floating point precision for the value to be displayed
    :max_T_val: Value above which display switches to :inf_str:
    :min_p_val: Value below which display switches to :zero_str:
    :inf_str: String to display when T is virtually infinite
    (or simply larger than max_T_val)
    :zero_str: String to display when p is virtually null
    (or simply smaller than min_p_val)
    :unit: Optional unit
    """
    
    fmt = f".{fp}f"

    if np.isnan(value):
        return "NaN"
    # Only T can be greater than 1
    elif np.isinf(value) or value >= max_T_val:
        return inf_str
    # Only p can be smaller than 1
    elif value <= min_p_val:
        return " ".join([zero_str, unit])
    elif value <= pow(10, -fp):
        return " ".join([f"< {pow(10, -fp)}", unit])
    else:
        return " ".join([format(value, fmt), unit])
        


# TODO Make interactive plot
def plot_probability(stats: xr.DataArray):

    # 1. Calcul des quantiles
    qstats = stats.quantile(
        [0.5*CONFIDENCE_INTERVAL, 0.5, 1-0.5*CONFIDENCE_INTERVAL],
        dim="sample_MCMC"
    ).assign_coords(quantile=["ql", "be", "qu"])

    # 2. Définition des tailles
    mm = 1. / 25.4
    ratio = 16 / 11
    width = 180 * mm * 110  # 96 dpi
    height = width / ratio

    colors = ['rgba(255,0,0,0.5)', 'rgba(0,0,255,0.5)']
    yticks = np.array([0,1e-12,1e-6,1e-3,1e-2,1/30,1/10,0.2,0.5,1])
    yticklabelsL = ["0", "10⁻¹²", "10⁻⁶", "10⁻³", "10⁻²", "1/30", "1/10", "1/5", "1/2", "1"]
    yticklabelsR = ["∞", "", "", "1000", "100", "30", "10", "5", "2", "1"]

    fig = go.Figure()

    names = ['pF', 'pC']
    trace_names = ['Factual', 'Counter-factual']

    fill_traces = []
    median_traces = []

    for i, (name, tn) in enumerate(zip(names, trace_names)):
        qp = qstats.loc[:, :, name]
        time = qp.time.values
        be = qp.sel(quantile='be').values
        ql = qp.sel(quantile='ql').values
        qu = qp.sel(quantile='qu').values

        # Trace inférieure
        lower = go.Scatter(
            x=time,
            y=plink(ql),
            mode='lines',
            line=dict(color=colors[i], width=0),
            showlegend=False,
            hoverinfo='skip',
            fill=None
        )
        # Trace supérieure avec fill
        upper = go.Scatter(
            x=time,
            y=plink(qu),
            mode='lines',
            line=dict(color=colors[i], width=0),
            fill='tonexty',
            fillcolor=colors[i],
            showlegend=False,
            hoverinfo='skip'
        )
        fill_traces.extend([lower, upper])

        # Courbe médiane
        median = go.Scatter(
            x=time,
            y=plink(be),
            customdata=np.stack([
                [_safe_str(p, fp=2) for p in be],
                [_safe_str(p, fp=2) for p in ql],
                [_safe_str(p, fp=2) for p in qu],
                [_safe_str(1/p, fp=1, inf_str='infinity', unit='years') for p in be],
                [_safe_str(1/p, fp=1, inf_str='infinity', unit='years') for p in qu],
                [_safe_str(1/p, fp=1, inf_str='infinity', unit='years') for p in ql]
            ], axis=-1),
            mode='lines',
            line=dict(color=colors[i], width=2),
            name=tn,
            legendrank=1-i,
            hovertemplate=(
                "<b>Year</b> : %{x}<br>" +
                "<b>Probability</b> : %{customdata[0]}<br>" +
                "<b>Confidence</b> : From %{customdata[1]} to %{customdata[2]}<br>" +
                "<b>Return period</b> : %{customdata[3]}<br>" +
                "<b>Confidence</b> : From %{customdata[4]} to %{customdata[5]}" +
                "<extra></extra>"
            )
        )
        median_traces.append(median)

    # Ajout des traces dans le bon ordre
    fig = go.Figure()
    for trace in fill_traces:
        fig.add_trace(trace)
    for trace in median_traces:
        fig.add_trace(trace)

    # Adding bare minimum trace to get a secondary axis
    fig.add_trace(go.Scatter(
        x=[min(time), max(time)],
        y=[min(be), max(be)],
        name="yaxis2 data",
        showlegend=False,
        line=dict(width=0, color='rgba(0,0,0,0)'),
        hoverinfo='skip',
        yaxis="y2"
    ))

    # 4. Mise en forme de l’axe principal Y
    fig.update_layout(
        width=width,
        height=height,
        meta=dict(initial_width=width, initial_height=height),
        margin=dict(l=60, r=60, t=40, b=40),
        yaxis=dict(
            title="Probability",
            tickvals=plink(yticks),
            ticktext=yticklabelsL,
            range=[plink(0), plink(1)],
            showline=True,
            linecolor='black',
            gridcolor='lightgrey',
            tickfont=dict(size=14, color='black'),
            title_font=dict(size=16, color='black', family='Arial')
        ),
        yaxis2=dict(
            title="Return period",
            overlaying='y',
            side='right',
            tickvals=plink(yticks),
            ticktext=yticklabelsR,
            showgrid=False,
            showline=True,
            range=[plink(0), plink(1)],
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
            font=dict(size=14)  # taille en pixels
        ),
        modebar_remove=['select', 'lasso2d']
    )

    return fig