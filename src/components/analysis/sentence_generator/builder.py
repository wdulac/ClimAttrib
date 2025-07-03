from dash import html, dcc
from datetime import datetime
from .loader import load_template, fill_template
from .formatter import format_prob, format_return_period, format_year
from .logic import should_include_today_phrase

def build_summary_component(stats):
    year = stats.attrs["time"]
    
    pF = float(stats['pF'].sel(time=year, quantile='BE'))
    pC = float(stats['pC'].sel(time=year, quantile='BE'))
    RF = float(stats['RF'].sel(time=year, quantile='BE'))
    RC = float(stats['RC'].sel(time=year, quantile='BE'))

    variables = {
        "year_then": format_year(year),
        "pF_then": format_prob(pF),
        "RP_F_then": format_return_period(RF),
        "RP_C_then": format_return_period(RC),
        "pC_then": format_prob(pC),
    }

    sentences = []

    intro = load_template("intro")
    sentences.append(fill_template(intro, variables))

    today = datetime.today().year

    if should_include_today_phrase(year, today):
        pF_today = stats['pF'].sel(time=today, quantile='BE')
        today_tpl = load_template("today_update")
        sentences.append(
            fill_template(
                today_tpl, {
                    "year_today": format_year(today),
                    "pF_today": format_prob(pF_today),
                    "pF_ratio_now_then": f"{(pF_today/pF):.1f}",
                    "year_then": variables.get('year_then')
                }
            )
        )

    # Markdown → HTML
    return html.Div(children=[
        dcc.Markdown(sentence) for sentence in sentences
    ])
