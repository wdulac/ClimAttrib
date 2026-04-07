import numpy as np

from .__numbers import (
    _fmt_sig,
    _round_to_n_sigfigs,
    _compact_notation,
)

from .__settings import (
    DEFAULT_SIG,

    PROB_SOFT_MIN,
    PROB_SOFT_MAX,

    RET_SOFT_MAX,

    DEFAULT_THOUSAND_SEP,

    PR_SOFT_MIN,
    PR_SOFT_MAX,

    FAR_SIG_SECONDARY,
    FAR_SIG_THRESHOLD,
    FAR_SOFT_MAX,
    FAR_NAN_STR
)

unbreakable_space = "\u00A0"


def format_probability(
        x: float,
        sig: int = DEFAULT_SIG,
        soft_min: float = PROB_SOFT_MIN,
        soft_max: float = PROB_SOFT_MAX
    ) -> str:
    """
    Converts a probability defined on [0, 1] into a formated percentage string rounded to :sig: significant digits.
    Handles: 
    * A soft min (expressed as a percentage) so that any x in ]0, :soft_min:[ returns "< :soft_min:"
    * A soft max (expressed as a percentage) so that any x in ]:soft_max:, 1[ returns "> :soft_max:"

    Any value in [:soft_min:, :soft_max:] returns _fmt_sig(100*x, sig=sig)

    Note that both 0 and 100 (%) are permitted values, distinct from either :soft_min: and :soft_max:
    """

    pct = 100 * x

    if pct > 0:
        if pct < 100:
            if pct > soft_max:
                upper_str = str(soft_max)
                s = ">" + unbreakable_space + upper_str
            elif pct >= soft_min:
                s = _fmt_sig(pct, sig=sig)
            else:
                # i.e 0 < pct < soft_min
                low_str = str(soft_min)
                s = "<" + unbreakable_space + low_str
        else:
            #i.e pct == 100 %
            s = _fmt_sig(pct, sig=sig)
    else:
        # i.e pct == 0
        s = _fmt_sig(pct)

    return s


def format_return_period(
        x: float,
        compact: bool = False,
        thousand_sep: str = DEFAULT_THOUSAND_SEP,
        sig: int = DEFAULT_SIG,
        soft_max: float = RET_SOFT_MAX
    ) -> str:
    """
    Converts a return period defined on [1, ∞] into a formated string rounded to :sig: significant digits.
    Handles:
    * Compact notation, e.g 1.2k for 1 200
    * Standard decimal notation with an arbitrary thousand sperator
    * A soft max so that any value in ]:soft_max:, ∞[ returns "> :soft_max:"
    """

    if x < np.inf:

        _x = _round_to_n_sigfigs(x, n=sig)

        if compact:

            if x > soft_max:
                soft_max_str = _compact_notation(soft_max, sig) # Use compact notation for :soft_max: as well
                s = ">" + unbreakable_space + soft_max_str
            else:
                s = _compact_notation(_x, sig)

        else:

            if x > soft_max:
                soft_max_str = _fmt_sig(soft_max, sig, thousand_sep=thousand_sep)
                s = ">" + unbreakable_space + soft_max_str
            else:
                s = _fmt_sig(_x, sig, thousand_sep=thousand_sep)

    else:
        # i.e x == np.inf
        s = _fmt_sig(x)

    return s


def format_probability_ratio(
        x: float,
        sig: int = DEFAULT_SIG,
        soft_min: float = PR_SOFT_MIN,
        soft_max: float = PR_SOFT_MAX,
        thousand_sep: int = DEFAULT_THOUSAND_SEP
    ) -> str:
    """
    Converts a probability ratio defined on [0, ∞] into a formatted string rounded to :sig: significant digits.
    Handles:
    * A soft min so that any x in ]0, :soft_min:[ returns "< :soft_min:"
    * A soft max so that any x in ]:soft_max:, ∞[ returns "> :soft_max:"

    0 and ∞ are permitted values and displayed as such.
    """
    
    if x > 0:
        if x < np.inf:
            if x > soft_max:
                upper_str = _fmt_sig(soft_max, sig, thousand_sep=thousand_sep)
                s = ">" + unbreakable_space + upper_str
            elif x >= soft_min:
                s = _fmt_sig(x, sig, thousand_sep=thousand_sep)
            else:
                # i.e x is in between ]0, :soft_min:[
                lower_str = _fmt_sig(soft_min, sig)
                s = "<" + unbreakable_space + lower_str
        else:
            # i.e x is in fact np.inf -> let _fmt_sig handle it
            s = _fmt_sig(x)
    else:
        # i.e x is in fact 0 -> let _fmt_sig handle it
        s = _fmt_sig(x)

    return s


def format_fraction_of_attributable_risk(
        x: float,
        sig: int = DEFAULT_SIG,
        sig_secondary: int = FAR_SIG_SECONDARY,
        sig_threshold: float = FAR_SIG_THRESHOLD,
        soft_max: float = FAR_SOFT_MAX,
        nan_str: str = FAR_NAN_STR
) -> str:
    """
    Converts a FAR defined on [0, 1] into a formated percentage string rounded to :sig: significant digits.
    Handles:
    * A soft max so that any x in ]:soft_max:, 1[ returns "> :soft_max:"
    * A FAR threshold above which the amount of significant digits differs (e.g 3 digits when above 99%, 2 otherwise)
    * Custom NaN string

    0 and 100 (%) are permitted values and are displayed as such (without unit)
    """

    pct = x * 100
    
    if pct < 100:
        if pct > soft_max:
            upper_str = str(soft_max)
            s = ">" + unbreakable_space + upper_str
        elif pct > sig_threshold:
            s = _fmt_sig(pct, sig=sig_secondary)
        else:
            s = _fmt_sig(pct, sig=sig)
    else:
        # FAR is either nan or 100 %
        if np.isnan(pct):
            s = _fmt_sig(pct, nan_str=nan_str)
        else:
            # FAR is 100 %
            s = _fmt_sig(pct, sig=sig)

    return s


def format_temperature(
        x: float,
        sig: int = DEFAULT_SIG,
        signed_notation : bool = False,
        force_one_decimal: bool = False
) -> str:
    """
    Converts a temperature into a formatted string rounded to :sig: significant digits

    Supports optional signed notation to reflect Deltas.
    """

    if force_one_decimal:
        if signed_notation:
            return f"{x:+.1f}"
        else:
            return f"{x:.1f}"

    # Cas standard avec chiffres significatifs
    s = _fmt_sig(x, sig=sig)

    if not signed_notation:
        return s
    
    if s.startswith('-'):
        return s
    else:
        return f"+{s}"