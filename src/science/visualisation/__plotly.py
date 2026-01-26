# For typing
import numpy as np
import xarray as xr
from collections.abc import Callable

import plotly.graph_objects as go


def create_attribution_plotly_graph(
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


def _clim_plots_base_layout(
    fig,
    xaxis_title: str | None = None,
    yaxis_title: str | None = None,
    cache_key: str | None = None,
):

    # Taille
    mm = 1. / 25.4
    ratio = 16 / 11
    width = 180 * mm * 110
    height = width / ratio

    fig.update_layout(
        width=width,
        height=height,
        plot_bgcolor="white",
        paper_bgcolor="#f1f3f5",
        margin=dict(l=60, r=40, t=40, b=40),
        legend=dict(
            orientation="h",
            y=1.02,
            x=0.5,
            xanchor="center",
        ),
        meta=dict(key=cache_key),
    )
    
    if xaxis_title:
        fig.update_xaxes(title=xaxis_title)
    
    if yaxis_title:
        fig.update_yaxes(title=yaxis_title)