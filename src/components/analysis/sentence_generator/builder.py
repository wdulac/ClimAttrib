from dash import html, dcc, clientside_callback, ClientsideFunction, Input, Output
from datetime import datetime
from .__loader import render_template, register_filters
from .__formatter import (
    format_prob_adaptive, format_return_period_adaptive, format_ratio_adaptive, format_far_adaptive,
    format_prob_ci, format_return_period_ci, format_PR_ci, format_FAR_ci
)
from .__logic import should_include_today_update


DEFAULT_LANG = "en"


def build_summary_component(stats, lang: str | None = DEFAULT_LANG):

    # Register formatting functions as filters usable in the .md templates
    register_filters(
        lang,
        format_prob=format_prob_adaptive,
        format_return_period=format_return_period_adaptive,
        format_year=lambda y: f"{int(y)}",
        format_PR=format_ratio_adaptive,
        format_FAR=format_far_adaptive,
        # CI-aware
        format_prob_ci=format_prob_ci,
        format_return_period_ci=format_return_period_ci,
        format_PR_ci=format_PR_ci,
        format_FAR_ci=format_FAR_ci
    )

    def q(ds, var, t, qlabel='BE'):
        return float(ds[var].sel(time=t, quantile=qlabel))

    def far_of(pr: float) -> float:
        # FAR = 1 - 1/PR ; garde la valeur brute (peut être < 0 si PR < 1)
        # protège la division si jamais PR≈0 (cas pathologique)
        return 1.0 - (1.0 / pr) if pr and abs(pr) > 1e-15 else float('nan')
    
    def safe_inv(x: float) -> float:
        return float('nan') if x is None or x == 0 else 1.0 / x

    year_then = stats.attrs["time"]
    today = datetime.today().year

       # --- BE (année de l'évènement) ---
    pF_be = q(stats, 'pF', year_then, 'BE')
    pC_be = q(stats, 'pC', year_then, 'BE')
    RF_be = q(stats, 'RF', year_then, 'BE')
    RC_be = q(stats, 'RC', year_then, 'BE')
    PR_be = q(stats, 'PR', year_then, 'BE')
    FAR_be = far_of(PR_be)

    # --- QL / QU (année de l'évènement) ---
    pF_ql, pF_qu = q(stats, 'pF', year_then, 'QL'), q(stats, 'pF', year_then, 'QU')
    pC_ql, pC_qu = q(stats, 'pC', year_then, 'QL'), q(stats, 'pC', year_then, 'QU')
    RF_ql, RF_qu = q(stats, 'RF', year_then, 'QL'), q(stats, 'RF', year_then, 'QU')
    RC_ql, RC_qu = q(stats, 'RC', year_then, 'QL'), q(stats, 'RC', year_then, 'QU')
    PR_ql, PR_qu = q(stats, 'PR', year_then, 'QL'), q(stats, 'PR', year_then, 'QU')
    FAR_ql, FAR_qu = far_of(PR_ql), far_of(PR_qu)

    # --- Inverses pour PR_then (pour wording "less likely") ---
    PR_inv     = safe_inv(PR_be)
    PR_inv_ql  = safe_inv(PR_qu)  # inversion: bornes s’inversent
    PR_inv_qu  = safe_inv(PR_ql)

    # --- Today (BE + QL/QU) ---
    pF_today     = q(stats, 'pF', today, 'BE')
    pF_today_ql  = q(stats, 'pF', today, 'QL')
    pF_today_qu  = q(stats, 'pF', today, 'QU')

    PR_today     = q(stats, 'PR', today, 'BE')
    PR_today_ql  = q(stats, 'PR', today, 'QL')
    PR_today_qu  = q(stats, 'PR', today, 'QU')

    # Inverses pour PR_today
    PR_today_inv    = safe_inv(PR_today)
    PR_today_inv_ql = safe_inv(PR_today_qu)
    PR_today_inv_qu = safe_inv(PR_today_ql)

    FAR_today    = far_of(PR_today)
    FAR_today_ql = far_of(PR_today_ql)
    FAR_today_qu = far_of(PR_today_qu)

    # Ratios pF_today / pF_then (BE + QL/QU sur today ; dénominateur = BE à l’année de l’évènement)
    ratio_now_then    = pF_today    / pF_be if pF_be and abs(pF_be) > 1e-15 else float('nan')
    ratio_now_then_ql = pF_today_ql / pF_be if pF_be and abs(pF_be) > 1e-15 else float('nan')
    ratio_now_then_qu = pF_today_qu / pF_be if pF_be and abs(pF_be) > 1e-15 else float('nan')

    # Inverses pour le ratio (pour wording "times less/more likely" sans nombres < 1)
    ratio_now_then_inv    = safe_inv(ratio_now_then)
    ratio_now_then_inv_ql = safe_inv(ratio_now_then_qu)  # inversion des bornes
    ratio_now_then_inv_qu = safe_inv(ratio_now_then_ql)

    variables = {
        # repères temporels
        "year_then": year_then,
        "year_today": today,
        "has_had": "has" if year_then == today else "had",
        "change": "more" if PR_be > 1 else "less",

        # BE (intro)
        "pF_then": pF_be,
        "pC_then": pC_be,
        "RP_F_then": RF_be,
        "RP_C_then": RC_be,
        "PR_then": PR_be,
        "PR_then_inv": PR_inv,
        "FAR_then": FAR_be,

        # quantiles (intro, pour filtres *_ci)
        "pF_then_ql": pF_ql, "pF_then_qu": pF_qu,
        "pC_then_ql": pC_ql, "pC_then_qu": pC_qu,
        "RP_F_then_ql": RF_ql, "RP_F_then_qu": RF_qu,
        "RP_C_then_ql": RC_ql, "RP_C_then_qu": RC_qu,
        "PR_then_ql": PR_ql, "PR_then_qu": PR_qu,
        "PR_then_inv_ql": PR_inv_ql, "PR_then_inv_qu": PR_inv_qu,
        "FAR_then_ql": FAR_ql, "FAR_then_qu": FAR_qu,

        # today_update (BE + QL/QU)
        "pF_today": pF_today,
        "pF_today_ql": pF_today_ql, "pF_today_qu": pF_today_qu,
        "PR_today": PR_today,
        "PR_today_ql": PR_today_ql, "PR_today_qu": PR_today_qu,
        "PR_today_inv": PR_today_inv,
        "PR_today_inv_ql": PR_today_inv_ql, "PR_today_inv_qu": PR_today_inv_qu,
        "FAR_today": FAR_today,
        "FAR_today_ql": FAR_today_ql, "FAR_today_qu": FAR_today_qu,

        # ratios (et inverses)
        "pF_ratio_now_then":            ratio_now_then,
        "pF_ratio_now_then_ql":         ratio_now_then_ql,
        "pF_ratio_now_then_qu":         ratio_now_then_qu,
        "pF_ratio_now_then_inv":        ratio_now_then_inv,
        "pF_ratio_now_then_inv_ql":     ratio_now_then_inv_ql,
        "pF_ratio_now_then_inv_qu":     ratio_now_then_inv_qu,

        # libellés
        "change_PR_today": "more" if PR_today > 1 else "less",
        "change_today": "an increase" if ratio_now_then > 1 else "a decrease",
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
        FAR_today = 1 - (1/PR_today)
        paragraphs.append(
            render_template("today_update", variables, lang=lang)
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
