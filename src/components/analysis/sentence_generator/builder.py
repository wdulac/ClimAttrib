from dash import html, dcc, clientside_callback, ClientsideFunction, Input, Output
from datetime import datetime
from .__loader import render_template, register_filters
from .__formatter import (
    format_prob, format_return_period, format_year, format_PR, format_FAR
)
from .__logic import should_include_today_update


DEFAULT_LANG = "en"


def build_summary_component(stats, lang: str | None = DEFAULT_LANG):

    # Register formatting functions as filters usable in the .md templates
    register_filters(
        lang,
        format_prob=format_prob,
        format_return_period=format_return_period,
        format_year=format_year,
        format_PR=format_PR,
        format_FAR=format_FAR,
    )

    year_then = stats.attrs["time"]
    pF_then = float(stats['pF'].sel(time=year_then, quantile='BE'))
    pC_then = float(stats['pC'].sel(time=year_then, quantile='BE'))
    RF_then = float(stats['RF'].sel(time=year_then, quantile='BE'))
    RC_then = float(stats['RC'].sel(time=year_then, quantile='BE'))
    PR_then = float(stats['PR'].sel(time=year_then, quantile='BE'))
    FAR_then = 1 - (1/PR_then)
    today = datetime.today().year

    variables = {
        "year_then": year_then,
        "pF_then": pF_then,
        "RP_F_then": RF_then,
        "RP_C_then": RC_then,
        "pC_then": pC_then,
        "PR_then": PR_then,
        "FAR_then": FAR_then,
        "change": "more" if PR_then > 1 else "less",
        "has_had": "has" if year_then == today else 'had'
    }

    paragraphs: list[str] = []

    # Paragraphe d'introduction
    paragraphs.append(
        render_template("intro", variables, lang=lang)
    )

    if should_include_today_update(year_then, today):
        # Lookup updated quantities
        pF_today = float(stats['pF'].sel(time=today, quantile='BE'))
        PR_today = float(stats['PR'].sel(time=today, quantile='BE'))
        ratio_now_then = pF_today/pF_then
        FAR_today = 1 - (1/PR_today)
        paragraphs.append(
            render_template(
                "today_update", {
                    "year_today": today,
                    "year_then": variables.get('year_then'),
                    "pF_today": pF_today,
                    "pF_ratio_now_then": ratio_now_then,
                    "PR_today": PR_today,
                    "FAR_today": FAR_today,
                    "change": "an increase" if ratio_now_then > 1 else "a decrease",
                    "change_PR_today": "more" if PR_today > 1 else "less"
                },
                lang=lang
            )
        )

    # Markdown → HTML
    return html.Div(children=[
        dcc.Markdown(paragraph) for paragraph in paragraphs
    ], style={'userSelect': 'text', 'width': '70%'}, id='generated-sentences')


clientside_callback(
    ClientsideFunction(
        namespace='carousel',
        function_name='blockSwiper'
    ),
    Output('my-carousel', 'data-generated-sentences'),
    Input('generated-sentences', 'id')
)
