import numpy as np

from .__numbers import _fmt_sig, _round_to_n_sigfigs
from .__settings import (
    DEFAULT_SIG,
    PROB_SOFT_MIN,
    PROB_SOFT_MAX,
    RET_SOFT_MAX
)

unbreakable_space = "\u00A0"


def _probability(
        x: float,
        sig: int = DEFAULT_SIG,
        soft_min: float = PROB_SOFT_MIN,
        soft_max: float = PROB_SOFT_MAX
    ) -> str:
    """
    Formats a probability defined on [0, 1] into a formated percentage string rounded to :sig: significant digits.
    Handles: 
    * A soft min (expressed as a percentage) so that any x in ]0, :soft_min:[ returns "< :soft_min:"
    * A soft max (expressed as a percentage) so that any x in ]:soft_max:, 1[ returns "> :soft_max:"

    Any value in [:soft_min:, :soft_max:] returns _fmt_sig(100*x, sig=sig)

    Note that both 0 and 100 (%) are permitted values, distinct from either :soft_min: and :soft_max:
    """

    pct = 100 * x

    if pct > 0:
        if pct > soft_max:
            upper_str = str(soft_max)
            s = ">" + unbreakable_space + upper_str
        elif pct >= soft_min:
            s = _fmt_sig(pct, sig=sig)
        else:
            # i.e pct < soft_min
            low_str = str(soft_min)
            s = "<" + unbreakable_space + low_str
    else:
        # i.e pct == 0
        s = _fmt_sig(pct)

    return s


def _return_period(
        x: float,
        compact: bool = False,
        thousand_sep: str | None = None,
        sig: int = DEFAULT_SIG,
        soft_max: float = RET_SOFT_MAX
    ) -> str:
    """
    Formats a return period defined on [1, ∞] into a formated string rounded to :sig: significant digits.
    Handles:
    * Compact notation, e.g 1.2k for 1 200
    * Standard decimal notation with an arbitrary thousand sperator
    * A soft max so that any value in ]:soft_max:, ∞[ returns "> :soft_max:"
    """

    if x < np.inf:

        _x = _round_to_n_sigfigs(x, n=sig)
        _soft_max = _round_to_n_sigfigs(soft_max, n=sig)

        if compact:

            def eval_compact_notation(val, sig=sig):

                if val < 1_000:
                    # valeurs < 1000 : nombre brut à 2 :sig: significatifs
                    s_val = _fmt_sig(val, sig=sig)
                    suffix = ""
                elif val < 1_000_000:
                    s_val = _fmt_sig(val / 1_000.0, sig=sig)
                    suffix = "k"
                elif val < 1_000_000_000:
                    s_val = _fmt_sig(val / 1_000_000.0, sig=sig)
                    suffix = "M"
                else:
                    s_val = _fmt_sig(val / 1_000_000_000.0, sig=sig)
                    suffix = "G"
                
                return f"{s_val}{suffix}"
            
            if x > soft_max:
                soft_max_str = eval_compact_notation(_soft_max) # Use compact notation for :soft_max: as well
                s = ">" + unbreakable_space + soft_max_str
            else:
                s = eval_compact_notation(_x)

        else:
            
            def eval_standard_notation(val):
                if val >= 1000:
                    v = int(round(val))
                    if thousand_sep is None:
                        return str(v)
                    else:
                        return f"{v:,}".replace(",", thousand_sep)
                else:
                    return _fmt_sig(val, sig=sig)


            if x > soft_max:
                soft_max_str = eval_standard_notation(_soft_max)
                s = ">" + unbreakable_space + soft_max_str
            else:
                s = eval_standard_notation(_x)

    else:
        # i.e x == np.inf
        s = _fmt_sig(x)

    return s