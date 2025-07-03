from dash import html, dcc
from datetime import datetime
from .loader import load_template, fill_template
from .formatter import format_prob, format_return_period, format_year, format_PR
from .logic import should_include_today_phrase

def build_summary_component(stats):
    year_then = stats.attrs["time"]
    
    pF_then = float(stats['pF'].sel(time=year_then, quantile='BE'))
    pC_then = float(stats['pC'].sel(time=year_then, quantile='BE'))
    RF_then = float(stats['RF'].sel(time=year_then, quantile='BE'))
    RC_then = float(stats['RC'].sel(time=year_then, quantile='BE'))
    PR_then = float(stats['PR'].sel(time=year_then, quantile='BE'))

    variables = {
        "year_then": format_year(year_then),
        "pF_then": format_prob(pF_then),
        "RP_F_then": format_return_period(RF_then),
        "RP_C_then": format_return_period(RC_then),
        "pC_then": format_prob(pC_then),
        "change": "more" if PR_then > 1 else "less",
        "PR_then": format_PR(PR_then)
    }

    sentences = []

    intro = load_template("intro")
    sentences.append(fill_template(intro, variables))

    today = datetime.today().year

    if should_include_today_phrase(year_then, today):
        pF_today = float(stats['pF'].sel(time=today, quantile='BE'))
        PR_today = float(stats['PR'].sel(time=today, quantile='BE'))
        ratio_now_then = pF_today/pF_then
        today_tpl = load_template("today_update")
        sentences.append(
            fill_template(
                today_tpl, {
                    "year_today": format_year(today),
                    "pF_today": format_prob(pF_today),
                    "pF_ratio_now_then": format_PR(ratio_now_then),
                    "PR_today": format_PR(PR_today),
                    "year_then": variables.get('year_then'),
                    "change": "an increase" if ratio_now_then > 1 else "a decrease",
                    "change_PR_today": "more" if PR_today > 1 else "less"
                }
            )
        )

    # Markdown → HTML
    return html.Div(children=[
        dcc.Markdown(sentence) for sentence in sentences
    ], style={'width': '70%'})
