import numpy as np
from .__data_models import CIValue

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

def ratio_phrase(ratio: CIValue, ratio_inv: CIValue, fmt_ratio):
    """
    Retourne :
    - mot ("increased" / "decreased")
    - valeur formatée
    """

    if ratio.value >= 1:
        return "increased", fmt_ratio(ratio)
    else:
        return "decreased", fmt_ratio(ratio_inv)


# =========================================================
# Phrase "impossible"
# =========================================================

def impossible_sentence(RP_C: CIValue):
    """
    Détecte si l'intervalle inclut l'infini
    """

    if np.isinf(RP_C.qu):
        return (
            "Given the uncertainty, it cannot be excluded that such an event "
            "would have been effectively impossible without human influence."
        )
    return ""