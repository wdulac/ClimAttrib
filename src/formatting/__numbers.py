import numpy as np
import math

from .__settings import DEFAULT_SIG, DEFAULT_THOUSAND_SEP


def _round_to_n_sigfigs(x: float, n: int = 2) -> float:
    """
    Round x to n significant figures.
    """

    if x == 0:
        return 0

    sign = 1 if x > 0 else -1
    x_abs = abs(x)

    exponent = math.floor(math.log10(x_abs))
    factor = 10 ** (exponent - (n - 1))

    return sign * round(x_abs / factor) * factor
    

def _fmt_sig(x: float, sig: int = 2, nan_str: str = "NaN", inf_str: str = "∞", thousand_sep: str = DEFAULT_THOUSAND_SEP) -> str:
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
    exponent = math.floor(math.log10(abs(_x)))
    decimals = max(0, sig - 1 - exponent)
    if thousand_sep:
        s = f"{_x:,.{decimals}f}"
        if thousand_sep != ",":
            s = s.replace(",", thousand_sep)
    else:
        s = f"{_x:.{decimals}f}"

    # Retire les trailing 0 (par exemple afficher 0.49 à 3 chiffres significatifs -> reste 0.49 et pas 0.490)
    if "." in s:
        s = s.rstrip("0").rstrip(".")

    return s


def _compact_notation(val: float, sig: int = DEFAULT_SIG):

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