"""
Phrase-building functions for the sentence generator.

Assembles the natural-language fragments that cannot be expressed as static template
text because they depend on the sign of a metric:

- ``attribution_then``, ``attribution_today``, ``attribution_future`` — produce the
  PR/FAR attribution phrase for each time horizon. When ``PR >= 1`` the phrase reads
  "X times more likely" and includes the FAR; when ``PR < 1`` it reads "X times less
  likely" using the inverse PR, with no FAR.
- ``ratio_phrase(ratio, ratio_inv, fmt, past_tense)`` — produces the
  "increased/decreased by X" phrase comparing two consecutive time horizons.
- ``impossible_sentence(pC)`` — returns a caveat sentence if the lower confidence
  bound of the counterfactual probability reaches zero.
- ``event_definition_phrase(duration, To, extreme_type)`` — produces the event
  description opening (e.g. "having a two-day average temperature of 42.3 °C or higher").
"""

import numpy as np
from .__data_models import CIValue

from formatting.metrics import format_temperature

# =========================================================
# PR + FAR (année de l'événement)
# =========================================================

def attribution_then(PR, PR_inv, FAR, fmt_PR, fmt_FAR):

    if PR.value >= 1:
        pr_str = f"{fmt_PR(PR)} more likely"
        far_value = fmt_FAR(FAR)
        has_far = True
    else:
        pr_str = f"{fmt_PR(PR_inv)} less likely"
        far_value = ""
        has_far = False

    return pr_str, far_value, has_far


# =========================================================
# PR + FAR (today)
# =========================================================

def attribution_today(PR: CIValue, PR_inv: CIValue, FAR: CIValue, fmt_PR, fmt_FAR):
    """
    Retourne :
    - PR_today_phrase
    - FAR_today (string ou vide)
    """

    if PR.value >= 1:
        pr_str = f"{fmt_PR(PR)} more likely"
        far_str = fmt_FAR(FAR)
        has_far = True
    else:
        pr_str = f"{fmt_PR(PR_inv)} less likely"
        far_str = ""
        has_far = False

    return pr_str, far_str, has_far


# =========================================================
# PR + FAR (future)
# =========================================================

def attribution_future(PR: CIValue, PR_inv: CIValue, FAR: CIValue, fmt_PR, fmt_FAR):
    """
    Retourne :
    - PR_future_phrase
    - FAR_future (string ou vide)
    """

    if PR.value >= 1:
        pr_str = f"{fmt_PR(PR)} more likely"
        far_str = fmt_FAR(FAR)
        has_far = True
    else:
        pr_str = f"{fmt_PR(PR_inv)} less likely"
        far_str = ""
        has_far = False

    return pr_str, far_str, has_far


# =========================================================
# Ratio de probabilité (today vs then, future vs today)
# =========================================================

def ratio_phrase(ratio: CIValue, ratio_inv: CIValue, fmt_ratio, past_tense: bool = True):
    """
    Retourne :
    - mot ("increase" / "decrease") avec conjugaison au passé en option
    - valeur formatée
    """

    if ratio.value >= 1:
        word, formatted_value = "increase", fmt_ratio(ratio)
    else:
        word, formatted_value = "decrease", fmt_ratio(ratio_inv)

    if past_tense:
        word += "d"

    return word, formatted_value


# =========================================================
# Phrase "impossible"
# =========================================================

def impossible_sentence(pC: CIValue):
    """
    Détecte si l'intervalle contre-factuel inclut le 0
    """

    if pC.ql == 0.0:
        return (
            "Given the uncertainty, it cannot be excluded that such an event "
            "would have been effectively impossible without human influence."
        )
    return ""


# =========================================================
# Phrase de définition de l'événement
# =========================================================

def event_definition_phrase(duration: int, To: float, extreme_type: str):

    num2words = {
        '1': 'one',
        '2': 'two',
        '3': 'three',
        '4': 'four',
        '5': 'five',
        '7': 'seven',
        '10': 'ten',
        '14': 'fourteen'
    }

    duration_str = f"{num2words[str(duration)]}-day"
    temp_then_factual = f"{format_temperature(To, force_one_decimal=True)}\u00A0°C"
    higher_or_lower = {"hot": "higher", "cold": "lower"}[extreme_type]

    event_definition = f"having a {duration_str} average temperature of {temp_then_factual} or {higher_or_lower}"

    return event_definition