import xarray as xr
import numpy as np
import sys

from collections.abc import Callable
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
    
        
def _safe_PR(value, max_val=1e5, min_val=1e-3):
    if np.isnan(value):
        return "NaN"
    elif value >= max_val:
        return f"> {int(max_val):,}".replace(",", " ")
    elif value > 1:
        if value < 10:
            return f"{value:.2f}"
        elif value < 20:
            return f"{value:.1f}"
        elif value < 100:
            return str(round(value))
        elif value < 1000:
            return str(round(value / 5) * 5)
        elif value < 10_000:
            return str(round(value / 50) * 50)
        else:
            return str(round(value / 500) * 500)
    elif value >= 0.01:
        return f"{value:.2f}"
    elif value < min_val:
        return f"< {min_val:.3f}"
    else:
        return f"{value:.3f}"


def _safe_FAR(value):

    if np.isnan(value):
        return "NaN"
    elif value < 0:
        return "--"
    
    p = value * 100
    if round(p, 2) > 99.99:
        return "> 99.99%"
    else:
        return f"{p:.2f}%"
    

def _safe_intensity(value):

    if np.isnan(value):
        return "NaN"
    
    return f"{value:.1f}°C"


def _safe_intensity_change(value):

    if np.isnan(value):
        return "NaN"
    
    return f"{value:+.1f}°C"


def create_plotly_figure(
    stats: xr.DataArray,
    variables: list[str],
    task_id: str,
    yaxis_conf: list[dict],
    xaxis_domain : list[float] = [0, 1],
    labels: list[str] | None = None,
    transform_func: Callable[[np.ndarray], float] | None = lambda x: x,
    customdata_func: Callable[[np.ndarray], np.ndarray] | None = None,
    hovermode: str | None = None,
    hovertemplate: str | None = None,
    colors: list[str] | None = ['255,0,0', '0,0,255', '0,128,0', '128,0,128'],
    fill_alpha: float = 0.5,
    line_alpha: float = 0.8,
    background_alpha: float = 0.3,
    title: str = ""
) -> go.Figure:

    # Taille
    mm = 1. / 25.4
    ratio = 16 / 11
    width = 180 * mm * 110
    height = width / ratio

    # Couleurs
    colors_fill = [f'rgba({c},{fill_alpha})' for c in colors][:len(variables)]
    colors_line = [f'rgba({c},{line_alpha})' for c in colors][:len(variables)]
    colors_hl =  [f'rgba({c},{background_alpha})' for c in colors][:len(variables)]

    fig = go.Figure()
    fill_traces, line_traces = [], []
    
    for i, var in enumerate(variables):
        ql = stats[var].sel(quantile="QL").values
        be = stats[var].sel(quantile="BE").values
        qu = stats[var].sel(quantile="QU").values
        time = stats.time.values
        label = labels[i] if labels else None

        # Traces IC
        lower = go.Scatter(
            x=time, y=transform_func(ql), mode='lines', line=dict(width=0),
            fill=None, hoverinfo='skip', showlegend=False
        )
        upper = go.Scatter(
            x=time, y=transform_func(qu), mode='lines', line=dict(width=0),
            fill='tonexty', fillcolor=colors_fill[i],
            hoverinfo='skip', showlegend=False
        )
        fill_traces += [lower, upper]

        # Trace médiane
        customdata = customdata_func(ql, be, qu) if customdata_func else None

        median = go.Scatter(
            x=time,
            y=transform_func(be),
            mode='lines',
            line=dict(color=colors_line[i], width=2),
            name=label,
            customdata=customdata,
            legendrank=1-i,
            hovertemplate=hovertemplate,
            showlegend=labels is not None,
            hoverlabel=dict(
                bgcolor=colors_hl[i],
                bordercolor='black',
                font=dict(color='black')
            )
        )
        line_traces.append(median)

    # Ajout dans le bon ordre
    for trace in fill_traces:
        fig.add_trace(trace)
    for trace in line_traces:
        fig.add_trace(trace)

    x0 = stats.attrs['time']
    fig.add_vline(
        x=x0,
        line={
            'color': 'black',
            'width': 1
        },
        annotation_text=f"Year {x0}",
        annotation_position='top left'
    )

    # Ajout d'un scatter invisible sur le deuxième axe, si ce dernier existe
    if len(yaxis_conf) > 1:
        fig.add_trace(
            go.Scatter(
                x=[min(time), max(time)],
                y=[min(be), max(be)],
                yaxis="y2",
                mode="markers",
                opacity=0,
                showlegend=False,
                hoverinfo="skip"
            )
        )

    # Mise en forme des axes (primaire obligatoire, secondaire optionnel)
    layout_yaxes = {}
    for i, yaxis in enumerate(yaxis_conf):
        axis_key = "yaxis" if i == 0 else "yaxis2"
        layout_yaxes[axis_key] = dict(
            title=yaxis.get("title", ""),
            tickvals=transform_func(yaxis.get("tickvals", None)),
            ticktext=yaxis.get("ticktext", None),
            tickformat=yaxis.get("tickformat", None),
            overlaying=yaxis.get("overlaying", "y" if i > 0 else None),
            side=yaxis.get("side", "left"),
            showline=True,
            linecolor='black',
            gridcolor='lightgrey' if i == 0 else None,
            showgrid=(i == 0),
            zeroline=(i == 0),
            zerolinecolor='lightgrey',
            zerolinewidth=1,
            tickfont=dict(size=14, color='black'),
            title_font=dict(size=16, color='black', family='Arial'),
            range=transform_func(yaxis.get("range", None)),
            domain=[0,1]
        )

    height = height + 13 if labels else height
    # Layout final
    fig.update_layout(
        width=width,
        height=height,
        meta=dict(
            initial_width=width,
            initial_height=height,
            task_id=task_id,
            variables='_'.join(variables)
        ),
        margin=dict(l=60, r=60, t=40, b=40),
        plot_bgcolor='white',
        paper_bgcolor='#f1f3f5',
        hovermode=hovermode,
        legend=dict(
            orientation="h",
            y=1.02,
            x=0.5,
            xanchor="center",
            yanchor="bottom",
            bgcolor='rgba(255,255,255,0)',
            font=dict(size=14),
            itemsizing='constant',
            traceorder='reversed',
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
            title_font=dict(size=16, color='black', family='Arial'),
            domain=xaxis_domain
        ),
        modebar_remove=['select', 'lasso2d'],
        **layout_yaxes
    )

    return fig


def plot_probability(stats: xr.DataArray, task_id: str) -> go.Figure:

    yticks = np.array([EPSILON,1e-6,1e-3,1e-2,1/40,1/10,0.25,0.5,1-EPSILON])
    yticklabelsL = ["0", "0,0001%", "0,1%", "1%", "2,5%", "10%", "25%", "50%", "100%"]
    yticklabelsR = ["∞", "1 000 000", "1000", "100", "40", "10", "4", "2", "1"]

    fig = create_plotly_figure(
        stats,
        variables=['pF', 'pC'],
        task_id=task_id,
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
        customdata_func=lambda ql, be, qu: np.stack([
            [_safe_prob(p) for p in be],
            [_safe_prob(p) for p in ql],
            [_safe_prob(p) for p in qu],
            [_safe_ret(1/p) for p in be],
            [_safe_ret(1/p) for p in qu],
            [_safe_ret(1/p) for p in ql]
        ], axis=-1),
        hovermode='x unified',
        hovertemplate=(
            # "<b>Year</b> : %{x}<br>" +
            "<b>Probability</b> : %{customdata[0]} <i>[%{customdata[1]} to %{customdata[2]}]</i><br>" +
            "<b>Return period</b> : %{customdata[3]} <i>[%{customdata[4]} to %{customdata[5]}]</i><br>" +
            "<extra></extra>"
        )
    )

    return fig


def plot_PR_FAR(stats: xr.Dataset, task_id: str) -> go.Figure:
    
    yticks = np.array([EPSILON, 1e-3, 1e-2, 0.1, 0.2, 1, 5, 10, 100, 1000, 1/EPSILON])
    yticklabelsL = ["0", "1/1000", "1/100", "1/10", "1/5", "1", "5", "10", "100", "1000", "∞"]
    ytickslabelsR = ["", "", "", "", "", "0%", "80%", "90%", "99%", "99,99%", "100%"]

    fig = create_plotly_figure(
        stats,
        variables=['PR'],
        task_id=task_id,
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
        customdata_func=lambda ql, be, qu: np.stack([
            [_safe_PR(pr) for pr in ql],
            [_safe_PR(pr) for pr in be],
            [_safe_PR(pr) for pr in qu],
            [_safe_FAR(1-(1/pr)) for pr in ql],
            [_safe_FAR(1-(1/pr)) for pr in be],
            [_safe_FAR(1-(1/pr)) for pr in qu]
        ], axis=-1),
        hovermode='x unified',
        hovertemplate=(
            # "<b>Year</b> : %{x}<br>" +
            "<b>Ratio</b> : %{customdata[1]} <i>[%{customdata[0]} to %{customdata[2]}]</i><br>" +
            "<b>FAR</b> : %{customdata[4]} <i>[%{customdata[3]} to %{customdata[5]}]</i><br>" +
            "<extra></extra>"
        ),
        transform_func=PRlink
    )

    # Hachure de la région PR < 1
    y0 = PRlink(EPSILON)
    y1 = PRlink(1)

    x_start = stats.time.values[0]
    x_end = stats.time.values[-1]
    x_center = (x_start + x_end) / 2
    
    hachure_trace = go.Bar(
        x=[x_center],
        y=[y1 - y0],
        base=y0,
        width=[x_end - x_start],
        marker=dict(
            color="rgba(0,0,0,0)",
            pattern=dict(
                shape="/",
                fillmode="overlay",
                size=15,
                fgcolor="lightgrey",
            ),
            line=dict(width=0)
        ),
        hoverinfo="skip",
        showlegend=False,
        xaxis='x',
        yaxis='y'
    )
    
    # On l’ajoute en premier ou dernier selon ton besoin
    fig.add_trace(hachure_trace)

    fig.add_annotation(
        text="Fraction of attributable risk not interpretable for proba. ratio < 1",
        xref="paper", yref="y",
        x=0.9, y=PRlink(0.045),
        showarrow=False,
        font=dict(size=14, color="dimgrey")
    )

    return fig


def plot_intensity(stats: xr.Dataset, task_id: str) -> go.Figure:

    # Note to self: If this somehow causes issues (e.g offset subtracted multiple times) 
    # the alternative would be to add an offset parameter to the :create_plotly_figure: function.
    stats['IF'] -= 273.15
    stats['IC'] -= 273.15

    fig = create_plotly_figure(
        stats,
        variables=['IF', 'IC'],
        task_id=task_id,
        yaxis_conf=[{
            'title': 'Event intensity [°C]'
        },
        {'side': 'right', 'tickvals': [], 'ticktext': []}],
        labels=[
            'With human influence',
            'Without human influence'
        ],
        customdata_func=lambda ql, be, qu: np.stack([
            [_safe_intensity(t) for t in ql],
            [_safe_intensity(t) for t in be],
            [_safe_intensity(t) for t in qu],
        ], axis=-1),
        hovermode='x unified',
        hovertemplate=(
            "%{customdata[1]} <i>[%{customdata[0]} to %{customdata[2]}]</i>" +
            "<extra></extra>"
        )
    )

    return fig


def plot_intensity_change(stats: xr.Dataset, task_id: str) -> go.Figure:

    fig = create_plotly_figure(
        stats,
        variables=['dI'],
        task_id=task_id,
        yaxis_conf=[{
            'title': 'Change in intensity [°C]',
            'tickformat': '+'
        },
        {'side': 'right', 'tickvals': [], 'ticktext': []}],
        customdata_func=lambda ql, be, qu: np.stack([
            [_safe_intensity_change(delta) for delta in ql],
            [_safe_intensity_change(delta) for delta in be],
            [_safe_intensity_change(delta) for delta in qu]
        ], axis=-1),
        hovermode='x unified',
        hovertemplate=(
            # "<b>Year</b> : %{x}<br>" +
            "<b>Change</b> : %{customdata[1]} <i>[%{customdata[0]} to %{customdata[2]}]</i>" +
            "<extra></extra>"
        ),
        colors=["204,85,0"]
    )

    return fig
