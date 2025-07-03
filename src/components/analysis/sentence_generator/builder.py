from dash import html, dcc, clientside_callback, ClientsideFunction, Input, Output
from datetime import datetime
from .loader import load_template, fill_template
from .formatter import format_prob, format_return_period, format_year, format_PR, format_FAR
from .logic import should_include_today_phrase

def build_summary_component(stats):

    year_then = stats.attrs["time"]
    pF_then = float(stats['pF'].sel(time=year_then, quantile='BE'))
    pC_then = float(stats['pC'].sel(time=year_then, quantile='BE'))
    RF_then = float(stats['RF'].sel(time=year_then, quantile='BE'))
    RC_then = float(stats['RC'].sel(time=year_then, quantile='BE'))
    PR_then = float(stats['PR'].sel(time=year_then, quantile='BE'))
    FAR_then = 1 - (1/PR_then)
    today = datetime.today().year

    variables = {
        "year_then": format_year(year_then),
        "pF_then": format_prob(pF_then),
        "RP_F_then": format_return_period(RF_then),
        "RP_C_then": format_return_period(RC_then),
        "pC_then": format_prob(pC_then),
        "PR_then": format_PR(PR_then),
        "FAR_then": format_FAR(FAR_then),
        "change": "more" if PR_then > 1 else "less",
        "has/had": "has" if year_then == today else 'had'
    }

    sentences = []

    intro = load_template("intro")
    sentences.append(fill_template(intro, variables))


    if should_include_today_phrase(year_then, today):
        pF_today = float(stats['pF'].sel(time=today, quantile='BE'))
        PR_today = float(stats['PR'].sel(time=today, quantile='BE'))
        ratio_now_then = pF_today/pF_then
        FAR_today = 1 - (1/PR_today)
        today_tpl = load_template("today_update")
        sentences.append(
            fill_template(
                today_tpl, {
                    "year_today": format_year(today),
                    "year_then": variables.get('year_then'),
                    "pF_today": format_prob(pF_today),
                    "pF_ratio_now_then": format_PR(ratio_now_then),
                    "PR_today": format_PR(PR_today),
                    "FAR_today": format_FAR(FAR_today),
                    "change": "an increase" if ratio_now_then > 1 else "a decrease",
                    "change_PR_today": "more" if PR_today > 1 else "less"
                }
            )
        )

    # Markdown → HTML
    return html.Div(children=[
        dcc.Markdown(sentence) for sentence in sentences
    ], style={'userSelect': 'text', 'width': '70%'}, id='generated-sentences')


clientside_callback(
    ClientsideFunction(
        namespace='carousel',
        function_name='blockSwiper'
    ),
    Output('my-carousel', 'data-generated-sentences'),
    Input('generated-sentences', 'id')
)
