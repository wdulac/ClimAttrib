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
    width = 180 * mm * 128  # 96 dpi
    height = width / ratio

    colors = ['rgba(255,0,0,0.5)', 'rgba(0,0,255,0.5)']
    yticks = np.array([0,1e-12,1e-6,1e-3,1e-2,1/30,1/10,0.2,0.5,1])
    yticklabelsL = ["0", "10⁻¹²", "10⁻⁶", "10⁻³", "10⁻²", "1/30", "1/10", "1/5", "1/2", "1"]
    yticklabelsR = ["∞", "", "", "1000", "100", "30", "10", "5", "2", "1"]

    fig = go.Figure()

    names = ['pF', 'pC']
    trace_names = ['Factual', 'Counter-factual']
    for i, (name, tn) in enumerate(zip(names, trace_names)):
        qp = qstats.loc[:, :, name]
        time = qp.time.values
        be = qp.sel(quantile='be').values
        ql = qp.sel(quantile='ql').values
        qu = qp.sel(quantile='qu').values

        # Bande inférieure
        fig.add_trace(go.Scatter(
            x=time,
            y=plink(ql),
            mode='lines',
            line=dict(color=colors[i], width=0),
            showlegend=False,
            hoverinfo='skip',
            fill=None
        ))

        # Bande supérieure
        fig.add_trace(go.Scatter(
            x=time,
            y=plink(qu),
            mode='lines',
            line=dict(color=colors[i], width=0),
            fill='tonexty',
            fillcolor=colors[i],
            # opacity=0.3,
            showlegend=False,
            hoverinfo='skip'
        ))

        # Courbe médiane
        fig.add_trace(go.Scatter(
            x=time,
            y=plink(be),
            customdata=np.stack([
                be,
                ql,
                qu,
                1/be,
                1/qu,
                1/ql
            ], axis=-1),
            mode='lines',
            line=dict(color=colors[i], width=2),
            name=tn,
            hovertemplate = (
                "<b>Year</b> : %{x}<br>" +
                "<b>Probability</b> : %{customdata[0]:.2f}<br>" +
                "<b>Confidence</b> : From %{customdata[1]:.2f} to %{customdata[2]:.2f}<br>" +
                "<b>Return period</b> : %{customdata[3]:.1f} years<br>" +
                "<b>Confidence</b> : From %{customdata[4]:.1f} to %{customdata[5]:.1f} years" +
                "<extra></extra>"
            )
        ))

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
        margin=dict(l=60, r=60, t=40, b=40),
        yaxis=dict(
            title="Probability",
            tickvals=plink(yticks),
            ticktext=yticklabelsL,
            range=[plink(0), plink(1)],
            showline=True,
            linecolor='black',
            gridcolor='lightgrey',
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
        ),
        xaxis=dict(
            title="Time",
            range=[1850, 2100],
            ticks='outside',
            showline=True,
            linecolor='black',
            gridcolor='lightgrey',
            mirror=True
        ),
        plot_bgcolor='white',
    )

    return fig