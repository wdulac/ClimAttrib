from .__data_models import CIValue
from .__formatters import _is_infinite_return_period


def safe_ci_format(ci: CIValue, formatter, **formatter_kargs):
    """Helper pour éviter répétition."""
    return formatter(ci.value, ci.ql, ci.qu, **formatter_kargs)


# =========================================================
# PR + FAR (année de l'événement)
# =========================================================

def attribution_then(PR, PR_inv, FAR, format_PR, format_FAR):

    if PR.value >= 1:
        pr_str = f"{safe_ci_format(PR, format_PR)} times more likely"
        far_value = safe_ci_format(FAR, format_FAR)
        has_far = True
    else:
        pr_str = f"{safe_ci_format(PR_inv, format_PR)} times less likely"
        far_value = ""
        has_far = False

    return pr_str, far_value, has_far


# =========================================================
# PR + FAR (today)
# =========================================================

def attribution_today(PR: CIValue, PR_inv: CIValue, FAR: CIValue,
                      format_PR, format_FAR):
    """
    Retourne :
    - PR_today_phrase
    - FAR_today (string ou vide)
    """

    if PR.value >= 1:
        pr_str = f"{safe_ci_format(PR, format_PR)} more likely"
        far_str = safe_ci_format(FAR, format_FAR)
        has_far = True
    else:
        pr_str = f"{safe_ci_format(PR_inv, format_PR)} less likely"
        far_str = ""
        has_far = False

    return pr_str, far_str, has_far


# =========================================================
# PR + FAR (future)
# =========================================================

def attribution_future(PR: CIValue, PR_inv: CIValue, FAR: CIValue,
                       format_PR, format_FAR):
    """
    Retourne :
    - PR_future_phrase
    - FAR_future (string ou vide)
    """

    if PR.value >= 1:
        pr_str = f"{safe_ci_format(PR, format_PR)} more likely"
        far_str = safe_ci_format(FAR, format_FAR)
        has_far = True
    else:
        pr_str = f"{safe_ci_format(PR_inv, format_PR)} less likely"
        far_str = ""
        has_far = False

    return pr_str, far_str, has_far


# =========================================================
# Ratio de probabilité (today vs then, future vs today)
# =========================================================

def ratio_phrase(ratio: CIValue, ratio_inv: CIValue, format_PR):
    """
    Retourne :
    - mot ("increased" / "decreased")
    - valeur formatée
    """

    if ratio.value >= 1:
        return "increased", safe_ci_format(ratio, format_PR, unit="")
    else:
        return "decreased", safe_ci_format(ratio_inv, format_PR, unit="")


# =========================================================
# Phrase "impossible"
# =========================================================

def impossible_sentence(RP_C: CIValue):
    """
    Détecte si l'intervalle inclut l'infini
    """

    if _is_infinite_return_period(RP_C.qu):
        return (
            "Given the uncertainty, it cannot be excluded that such an event "
            "would have been effectively impossible without human influence."
        )
    return ""