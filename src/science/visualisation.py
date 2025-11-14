import xarray as xr
import numpy as np
import math
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


def _round_to_n_sigfigs(x: float, n: int = 2) -> float:
    """Round x to n significant figures. Works for x > 0 and x < 0, returns 0.0 for x == 0."""
    if x == 0 or x is None or np.isnan(x):
        return 0.0
    sign = 1 if x > 0 else -1
    x_abs = abs(x)
    exponent = math.floor(math.log10(x_abs))
    factor = 10 ** (exponent - (n - 1))
    return sign * round(x / factor) * factor


def _fmt_sig_plot(x: float, sig: int = 2) -> str:
    """
    Version allégée pour Plotly :
    - pas de séparateur de milliers
    - pas de locale
    - pas d'espaces insécables
    """
    if np.isnan(x):
        return "NaN"
    if x == 0:
        return "0"

    rounded = _round_to_n_sigfigs(x, sig)
    mag = abs(rounded)

    # Si ~entier, on retourne un entier
    if mag >= 1 and abs(rounded - round(rounded)) < 1e-12:
        return str(int(round(rounded)))

    # sinon : décimales selon les sig figs
    digits_before = math.floor(math.log10(mag)) + 1 if mag >= 1 else 0
    decimals = max(0, sig - digits_before)
    s = f"{rounded:.{decimals}f}"

    # trim des zéros
    if "." in s:
        s = s.rstrip("0").rstrip(".")

    return s


def _safe_prob(value, fp=2, min_val=EPSILON, zero_str="0", unit="%"):
    """Probabilité p∈[0,1] -> pourcentage à fp chiffres significatifs (sur le %)."""
    if np.isnan(value):
        return "NaN"

    sig = fp  # on réutilise fp comme nb de chiffres significatifs sur le %
    pct = value * 100.0

    # ultra-petit -> zéro
    if 100 * value <= min_val:
        return f"{zero_str} {unit}" if unit else zero_str

    # borne basse : "< 0.01%" pour sig=2
    lower_display = 10 ** (-sig)
    if pct < lower_display:
        lower_str = _fmt_sig_plot(lower_display, sig)
        return f"< {lower_str}{unit if unit else ''}"

    # sinon : % avec sig chiffres significatifs
    s = _fmt_sig_plot(pct, sig)

    # si ça tombe sur 100 pile, on force "100"
    try:
        if abs(float(s) - 100.0) < 10 ** (-(sig + 1)):
            s = "100"
    except Exception:
        pass

    return f"{s}{unit if unit else ''}"



def _safe_ret(value, max_val=1/EPSILON, inf_str="infinity", unit="year"):
    """Durée de retour (années) avec 2 chiffres significatifs + suffixes k/M/G."""
    if np.isnan(value):
        return "NaN"
    if np.isinf(value) or value >= max_val:
        return inf_str

    v = float(value)

    # Choix de l'échelle pour k / M / G
    if v < 1_000:
        # valeurs < 1000 : nombre brut à 2 chiffres significatifs
        s_val = _fmt_sig_plot(v, 2)
        suffix = ""
    elif v < 1_000_000:
        s_val = _fmt_sig_plot(v / 1_000.0, 2)
        suffix = "k"
    elif v < 1_000_000_000:
        s_val = _fmt_sig_plot(v / 1_000_000.0, 2)
        suffix = "M"
    else:
        s_val = _fmt_sig_plot(v / 1_000_000_000.0, 2)
        suffix = "G"

    s = f"{s_val}{suffix}"
    plural = (unit + "s") if round(v, 1) > 1 else unit
    return f"{s} {plural}" if unit else s

        
def _safe_PR(value, max_val=1e5, min_val=1e-3):
    """PR avec 2 chiffres significatifs + bornes min/max numériques."""
    if np.isnan(value):
        return "NaN"

    v = float(value)

    # borne haute : "> max_val"
    if v >= max_val:
        # on garde l'affichage avec espace comme avant
        return f"> {int(max_val):,}".replace(",", " ")

    # borne basse : "< min_val"
    if v < min_val:
        min_str = _fmt_sig_plot(min_val, 2)
        return f"< {min_str}"

    # entre les bornes : 2 chiffres significatifs
    rounded = _round_to_n_sigfigs(v, 2)

    # pour des valeurs très grandes, on peut éventuellement regrouper,
    # mais ici on reste simple (pas de k/M/G pour PR)
    s = _fmt_sig_plot(rounded, 2)
    return s


def _safe_FAR(value):
    """
    FAR en %, style numérique :
    - FAR < 0.01%     -> '< 0.01%'
    - 0.01% <= FAR <= 99%  -> 2 sig figs
    - 99% < FAR < 99.9%    -> 3 sig figs
    - FAR >= 99.9%         -> '> 99.9%'
    """
    if np.isnan(value):
        return "NaN"
    if value < 0:
        return "--"

    p = float(value) * 100.0

    # borne basse
    if p < 0.01:
        return "< 0.01%"

    # borne haute
    if p >= 99.9:
        return "> 99.9%"

    # entre 99 et 99.9 : 3 chiffres significatifs
    if p > 99.0:
        sig = 3
    else:
        sig = 2

    s = _fmt_sig_plot(p, sig)
    return f"{s}%"


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
    cache_key: str,
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
            key=cache_key,
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


def plot_probability(stats: xr.DataArray, cache_key: str) -> go.Figure:

    yticks = np.array([EPSILON,1e-6,1e-3,1e-2,1/40,1/10,0.25,0.5,1-EPSILON])
    yticklabelsL = ["0", "0,0001%", "0,1%", "1%", "2,5%", "10%", "25%", "50%", "100%"]
    yticklabelsR = ["∞", "1 000 000", "1000", "100", "40", "10", "4", "2", "1"]

    fig = create_plotly_figure(
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


def plot_PR_FAR(stats: xr.Dataset, cache_key: str) -> go.Figure:
    
    yticks = np.array([EPSILON, 1e-3, 1e-2, 0.1, 0.2, 1, 5, 10, 100, 1000, 1/EPSILON])
    yticklabelsL = ["0", "1/1000", "1/100", "1/10", "1/5", "1", "5", "10", "100", "1000", "∞"]
    ytickslabelsR = ["", "", "", "", "", "0%", "80%", "90%", "99%", "99,99%", "100%"]

    fig = create_plotly_figure(
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


def plot_intensity(stats: xr.Dataset, cache_key: str) -> go.Figure:

    # Note to self: If this somehow causes issues (e.g offset subtracted multiple times) 
    # the alternative would be to add an offset parameter to the :create_plotly_figure: function.
    stats['IF'] -= 273.15
    stats['IC'] -= 273.15

    fig = create_plotly_figure(
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


def plot_intensity_change(stats: xr.Dataset, cache_key: str) -> go.Figure:

    fig = create_plotly_figure(
        stats,
        variables=['dI'],
        cache_key=cache_key,
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
