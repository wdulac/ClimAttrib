from dash import html
from science import compute_event_stats
from science import plot_probability

import matplotlib.pyplot as plt
import matplotlib.figure
from io import BytesIO
import base64


def _fig_to_uri(in_fig: matplotlib.figure.Figure, close_all=True, **save_args) -> str:
    """
    Save a figure as a URI
    :param in_fig:
    :return:
    """
    out_img = BytesIO()
    in_fig.savefig(out_img, format='png', **save_args)
    if close_all:
        in_fig.clf()
        plt.close('all')
    out_img.seek(0)  # rewind file
    encoded = base64.b64encode(out_img.read()).decode("ascii").replace("\n", "")
    return "data:image/png;base64,{}".format(encoded)


def probability_plot(event: dict):
    stats = compute_event_stats(event)
    fig, ax = plot_probability(stats)


    return html.Div(children=[
        html.Img(src=_fig_to_uri(fig))
    ], id='proba-plot')