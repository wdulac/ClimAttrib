import numpy as np
import math

from .__settings import DEFAULT_SIG


def _round_to_n_sigfigs(x: float, n: int = 2) -> float:
    """
    Round x to n significant figures.
    Does not expect any negative numbers.
    """

    if x > 0:
        exponent = math.floor(math.log10(x))
        factor = 10 ** (exponent - (n - 1))
        return round(x / factor) * factor
    elif x == 0:
        return 0
    

def _fmt_sig(x: float, sig: int = 2, nan_str: str = "NaN", inf_str: str = "∞") -> str:
    """
    Convert numbers to strings using :sig: significant digits.
    Uses decimal notation instead of scientific

    Handles:
    * Integers (e.g "1" instead of "1.0" if sig=2)
    * NaN and Infinity
    """

    if np.isnan(x):
        return nan_str
    if np.isinf(x):
        return inf_str
    
    # Arrondit le nombre à :sig: chiffres significatifs
    _x = _round_to_n_sigfigs(x, sig)
    if _x == 0:
        return "0"
    
    # Force l'affichage en décimales (non scientifique)
    exponent = math.floor(math.log10(_x))
    decimals = max(0, sig - 1 - exponent)
    s = f"{_x:.{decimals}f}"

    # Retire les trailing 0 (par exemple afficher 0.49 à 3 chiffres significatifs -> reste 0.49 et pas 0.490)
    if "." in s:
        s = s.rstrip("0").rstrip(".")

    return s


def _eval_standard_notation(val: float, sig: int = DEFAULT_SIG, thousand_sep: str | None = None):
    if val >= 1000:
        v = int(round(val))
        if thousand_sep is None:
            return str(v)
        else:
            return f"{v:,}".replace(",", thousand_sep)
    else:
        return _fmt_sig(val, sig=sig)
    

def _eval_compact_notation(val: float, sig: int = DEFAULT_SIG):

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