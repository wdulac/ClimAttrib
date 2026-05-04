"""
Automated text generator — public entry point of the sentence generator sub-module.

``automated_text(event, stats, lang)`` selects a Jinja2 template based on the nature
of the event, fills it with formatted metric values extracted from the attribution
result, and returns a ``html.Div`` containing the rendered Markdown text.

## Template selection

Templates live under ``sentence_generator/templates/en/``:

- ``extreme/{method}/{extreme_type}`` — used when ``pF < 80%`` (rare event) or the
  event intensity is within 1 K of the annual maximum.
- ``non_extreme/very_common`` — used when the event is common (``pF >= 80%``) and
  not close to the annual maximum.
- ``non_extreme/out_of_bound`` — used when ``pF == 1.0`` (the event is below the
  model's detection threshold).

## Template context

The template receives pre-formatted strings for three time horizons:

- **then** — the year of the event.
- **today** — the current year (omitted when the event happened in the current year).
- **future** — 2050.

For each horizon the context includes: probability (pF, pC), return periods (RP_F,
RP_C), intensity shift (dI), counterfactual intensity (IC), a PR/FAR attribution
phrase, and ratio phrases comparing consecutive horizons. All values include their
90% confidence interval formatted in IPCC bracket notation (e.g. ``4 [2 to 8] times``).
"""

from dash import html, dcc, clientside_callback, ClientsideFunction, Input, Output
from datetime import datetime
import xarray as xr

from .__data_models import CIValue
from .__metrics import build_metrics, invert_ci

from formatting import UNITS
from formatting.metrics import (
    format_probability,
    format_return_period,
    format_probability_ratio,
    format_fraction_of_attributable_risk,
    format_temperature
)

from .__phrases import (
    attribution_then,
    attribution_today,
    attribution_future,
    ratio_phrase,
    impossible_sentence,
    event_definition_phrase
)
from .__loader import render_template

from science.attribution.__data_loading import _load_obs


DEFAULT_LANG = "en"
EXTREME_PROB_THRESHOLD = 0.8 # 80 %
DISTANCE_FROM_MAX_THRESHOLD = 1.0 # Kelvin

YEAR_FOR_FUTURE_PARAGRAPH = 2050

def _fmt(ci, formatter, **kwargs):
    val = formatter(ci.value, **kwargs)
    low = formatter(ci.ql, **kwargs)
    high = formatter(ci.qu, **kwargs)

    unit_func = UNITS.get(formatter)

    if unit_func:
        unit = unit_func(ci.value)
        return f"**{val}\u00A0\[{low}\u00A0to\u00A0{high}\]\u00A0{unit}**"
    else:
        return f"**{val}\u00A0\[{low}\u00A0to\u00A0{high}\]**"
    

fmt_prob = lambda ci: _fmt(ci, format_probability)
fmt_RP = lambda ci: _fmt(ci, format_return_period)
fmt_PR = lambda ci: _fmt(ci, format_probability_ratio)
fmt_FAR = lambda ci: _fmt(ci, format_fraction_of_attributable_risk)
fmt_temp = lambda ci: _fmt(ci, format_temperature, force_one_decimal=True)


def automated_text(event: dict, stats: xr.Dataset, lang: str | None = DEFAULT_LANG):

    ## Evaluate which template to use...

    # Is the selected event extreme ? Check for pF and compare to Yo series
    prob = float(stats['pF'].sel(time=event['date'].year, quantile='BE'))

    if prob == 1.0:
        template = "non_extreme/out_of_bound"

    else:
        isExtreme = True
        if prob >= EXTREME_PROB_THRESHOLD:
            # Not rare but maybe still a maxima, therefore extreme
            Yo = _load_obs(event['lat'], event['lon'],
                        event['extreme_type'], event['method'],
                        event['start_date'], event['stop_date'],
                        event['duration'])
            
            Yo_year = event['date'].year
            # If Yo record is unavaiable for the selected year, use the last available Yo.
            if Yo_year > Yo.time.values[-1]:
                Yo_year = Yo.time.values[-1]
            isMax = abs(event['intensity'] - Yo.sel(time=Yo_year)) <= DISTANCE_FROM_MAX_THRESHOLD
            isExtreme = isMax
    
        if isExtreme:
            # Below :EXTREME_PROB_THRESHOLD: we consider the event rare enough to use the extreme templates
            template = f"extreme/{event['method']}/{event['extreme_type']}"
        else:
            template = "non_extreme/very_common"
    
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

    event_def = event_definition_phrase(
        event['duration'],
        event['intensity'] - 273.15,
        event['extreme_type']
    )

    context["event_definition"] = event_def

    context.update({
        "pF_then": fmt_prob(then.pF),
        "pC_then": fmt_prob(then.pC),
        "RP_F_then": fmt_RP(then.RP_F),
        "RP_C_then": fmt_RP(then.RP_C),
        "IC_then": fmt_temp(then.IC),
        "dI_then": fmt_temp(then.dI),
    })

    # PR / FAR
    pr_then, far_then, has_far_then = attribution_then(
        then.PR, then.PR_inv, then.FAR,
        fmt_PR, fmt_FAR
    )
    
    context.update({
        "PR_then_phrase": pr_then,
        "FAR_then": far_then,
        "has_far_then": has_far_then,
    })

    # Impossible
    context["impossible_sentence"] = impossible_sentence(then.pC)

    ## ======== Paragraphe TODAY ======== ##
    context["has_today"] = today is not None

    if today:
        context.update({
            "pF_today": fmt_prob(today.pF),
            "RP_F_today": fmt_RP(today.RP_F),
            "IF_today": fmt_temp(today.IF),
            "IC_today": fmt_temp(today.IC),
            "dI_today": fmt_temp(today.dI),
        })
    
        # PR / FAR
        pr_today, far_today, has_far_today = attribution_today(
            today.PR, today.PR_inv, today.FAR,
            fmt_PR, fmt_FAR
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
    
        word, value = ratio_phrase(ratio_today, ratio_today_inv, fmt_PR)
    
        context.update({
            "ratio_today_word": word,
            "ratio_today_value": value,
        })

    ## ======== Paragraphe FUTURE ======== ##
    context.update({
        "pF_future": fmt_prob(future.pF),
        "RP_F_future": fmt_RP(future.RP_F),
        "IF_future": fmt_temp(future.IF),
        "IC_future": fmt_temp(future.IC),
        "dI_future": fmt_temp(future.dI),
    })

    pr_future, far_future, has_far_future = attribution_future(
        future.PR, future.PR_inv, future.FAR,
        fmt_PR, fmt_FAR
    )
    
    context.update({
        "PR_future_phrase": pr_future,
        "FAR_future": far_future,
        "has_far_future": has_far_future,
    })

    # If today is not included, use `then` metrics for ratio_future
    if today:
        ratio_future = CIValue(
            value=future.pF.value / today.pF.value,
            ql=future.pF.ql / today.pF.value,
            qu=future.pF.qu / today.pF.value,
        )
    else:
        ratio_future = CIValue(
            value=future.pF.value / then.pF.value,
            ql=future.pF.ql / then.pF.value,
            qu=future.pF.qu / then.pF.value,
        )
    
    ratio_future_inv = invert_ci(ratio_future)

    word, value = ratio_phrase(ratio_future, ratio_future_inv, fmt_PR, past_tense=False)

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
