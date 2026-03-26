from dash import html, dcc, clientside_callback, ClientsideFunction, Input, Output
from datetime import datetime
import xarray as xr

from .__data_models import CIValue
from .__metrics import build_metrics, invert_ci
from .__formatters import (
    prob_with_CI,
    return_period_with_CI,
    PR_with_CI,
    FAR_with_CI,
    intensity_with_CI
)
from .__phrases import (
    attribution_then,
    attribution_today,
    attribution_future,
    ratio_phrase,
    impossible_sentence,
)
from .__loader import render_template

from science.attribution.__data_loading import _load_obs


DEFAULT_LANG = "en"
EXTREME_PROB_THRESHOLD = 0.8 # 80 %
DISTANCE_FROM_MAX_THRESHOLD = 1.0 # Kelvin

YEAR_FOR_FUTURE_PARAGRAPH = 2050

def _fmt(ci, formatter):
    return formatter(ci.value, ci.ql, ci.qu)

def automated_text(event: dict, stats: xr.Dataset, lang: str | None = DEFAULT_LANG):

    ## Evaluate which template to use...

    # Is the selected event extreme ? Check for pF and compare to Yo series
    isExtreme = True
    prob = float(stats['pF'].sel(time=event['date'].year, quantile='BE'))
    if prob >= EXTREME_PROB_THRESHOLD:
        # Not rare but maybe still a maxima, therefore extreme
        Yo = _load_obs(event['lat'], event['lon'],
                       event['extreme_type'], event['method'],
                       event['start_date'], event['stop_date'],
                       event['duration'])
        
        isMax = abs(event['intensity'] - Yo.sel(time=event['date'].year)) <= DISTANCE_FROM_MAX_THRESHOLD
        isExtreme = isMax
    
    if isExtreme:
        # Below :EXTREME_PROB_THRESHOLD: we consider the event rare enough to use the extreme templates
        template = f"extreme/{event['method']}/{event['extreme_type']}"
    else:
        template = "non_extreme/generic"
    
    ## Extract all necessary values to fill in the template

    # Separate time references for each paragraph
    year_then = event['date'].year
    year_today = datetime.today().year
    year_future = YEAR_FOR_FUTURE_PARAGRAPH

    # Extract all relevant metrics for each time reference
    then = build_metrics(stats, year_then)
    today = None
    if year_then < year_today:
        today = build_metrics(stats, year_today)
    future = build_metrics(stats, year_future)

    ### Build the context
    context = {
        "year_then": year_then,
        "year_today": year_today,
        "year_future": year_future,
    }

    ## ======== Paragraphe THEN ======== ##
    context.update({
        "pF_then": _fmt(then.pF, prob_with_CI),
        "pC_then": _fmt(then.pC, prob_with_CI),
        "RP_F_then": _fmt(then.RP_F, return_period_with_CI),
        "RP_C_then": _fmt(then.RP_C, return_period_with_CI),
        "IC_then": _fmt(then.IC, intensity_with_CI),
        "dI_then": _fmt(then.dI, intensity_with_CI),
    })

    # PR / FAR
    pr_then, far_then, has_far_then = attribution_then(
        then.PR, then.PR_inv, then.FAR,
        PR_with_CI, FAR_with_CI
    )
    
    context.update({
        "PR_then_phrase": pr_then,
        "FAR_then": far_then,
        "has_far_then": has_far_then,
    })

    # Impossible
    context["impossible_sentence"] = impossible_sentence(then.RP_C)

    ## ======== Paragraphe TODAY ======== ##
    context["has_today"] = today is not None

    if today:
        context.update({
            "pF_today": _fmt(today.pF, prob_with_CI),
            "RP_F_today": _fmt(today.RP_F, return_period_with_CI),
            "IF_today": _fmt(today.IF, intensity_with_CI),
            "IC_today": _fmt(today.IC, intensity_with_CI),
            "dI_today": _fmt(today.dI, intensity_with_CI),
        })
    
        # PR / FAR
        pr_today, far_today, has_far_today = attribution_today(
            today.PR, today.PR_inv, today.FAR,
            PR_with_CI, FAR_with_CI
        )
    
        context.update({
            "PR_today_phrase": pr_today,
            "FAR_today": far_today,
            "has_far_today": has_far_today,
        })
    
        # Ratio today / then
        ratio_today = CIValue(
            value=today.pF.value / then.pF.value,
            ql=today.pF.ql / then.pF.value,
            qu=today.pF.qu / then.pF.value,
        )
        ratio_today_inv = invert_ci(ratio_today)
    
        word, value = ratio_phrase(ratio_today, ratio_today_inv, PR_with_CI)
    
        context.update({
            "ratio_today_word": word,
            "ratio_today_value": value,
        })

    ## ======== Paragraphe FUTURE ======== ##
    context.update({
        "pF_future": _fmt(future.pF, prob_with_CI),
        "RP_F_future": _fmt(future.RP_F, return_period_with_CI),
        "IF_future": _fmt(future.IF, intensity_with_CI),
        "IC_future": _fmt(future.IC, intensity_with_CI),
        "dI_future": _fmt(future.dI, intensity_with_CI),
    })

    pr_future, far_future, has_far_future = attribution_future(
        future.PR, future.PR_inv, future.FAR,
        PR_with_CI, FAR_with_CI
    )
    
    context.update({
        "PR_future_phrase": pr_future,
        "FAR_future": far_future,
        "has_far_future": has_far_future,
    })

    ratio_future = CIValue(
        value=future.pF.value / today.pF.value,
        ql=future.pF.ql / today.pF.value,
        qu=future.pF.qu / today.pF.value,
    )
    ratio_future_inv = invert_ci(ratio_future)

    word, value = ratio_phrase(ratio_future, ratio_future_inv, PR_with_CI)

    context.update({
        "ratio_future_word": word,
        "ratio_future_value": value,
    })


    ## Render template and build component
    text = render_template(template, context)
    
    component = html.Div(children=[
        dcc.Markdown(text)
    ], style={'userSelect': 'text', 'width': '70%'}, id='generated-sentences')

    return component


clientside_callback(
    ClientsideFunction(
        namespace='carousel',
        function_name='blockSwiper'
    ),
    Output('my-carousel', 'data-generated-sentences'),
    Input('generated-sentences', 'id')
)
