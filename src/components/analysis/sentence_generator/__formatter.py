import math
import sys

EPSILON = 10 * sys.float_info.epsilon

# ---------- utilitaires ----------
def _is_nan(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


def _round_to_n_sigfigs(x: float, n: int = 2) -> float:
    """Round x to n significant figures. Works for x > 0 and x < 0, returns 0.0 for x == 0."""
    if x == 0 or x is None or _is_nan(x):
        return 0.0
    sign = 1 if x > 0 else -1
    x_abs = abs(x)
    exponent = math.floor(math.log10(x_abs))
    factor = 10 ** (exponent - (n - 1))
    return sign * round(x / factor) * factor


def _fmt_sig(x: float, sig: int = 2, thousands_sep: bool = True) -> str:
    """
    Format a number rounded to `sig` significant figures into a human-readable string:
    - Avoid scientific notation for common ranges.
    - Use grouping for large integers (via :,).
    - Trim trailing zeros and trailing dot.
    """
    if _is_nan(x):
        return "NaN"

    # Handle zero explicitly
    if x == 0:
        return "0"

    # if it's effectively an integer after rounding, show integer with grouping
    rounded = _round_to_n_sigfigs(x, sig)

    # For extremely small/large values, prefer plain decimal unless it would produce exponential format.
    # We'll decide based on magnitude:
    mag = abs(rounded)

    # If mag >= 1 and rounded is nearly integer, show integer with grouping
    if mag >= 1 and abs(rounded - round(rounded)) < 1e-12:
        return f"{int(round(rounded)):,}"

    # For moderate values use decimal without scientific notation:
    # Compute number of decimal places needed to represent rounded with no exponents:
    # We'll convert to string via format with enough precision, then trim.
    # Use 'f' with dynamic precision: compute digits after decimal as max(0, sig - digits_before_decimal)
    digits_before = math.floor(math.log10(mag)) + 1 if mag >= 1 else 0
    decimals = max(0, sig - digits_before)
    fmt = f"{{:.{decimals}f}}"
    s = fmt.format(rounded)

    # Trim trailing zeros and possible trailing dot
    if "." in s:
        s = s.rstrip("0").rstrip(".")

    # For thousands grouping on the integer part if requested
    if thousands_sep and "." in s:
        int_part, frac_part = s.split(".", 1)
        int_part = f"{int(int_part):,}"
        s = int_part + "." + frac_part
    elif thousands_sep and "." not in s and mag >= 1000:
        s = f"{int(round(rounded)):,}"

    return s


# ---------- formats adapted à 2 chiffres significatifs ----------
# (fp/sig = 2 par défaut, mais paramétrable)


def format_prob_adaptive(
    p: float,
    sig: int = 2,
    min_val: float = EPSILON,
    zero_str: str = "0",
    unit: str = "%",
) -> str:
    """
    Format a probability p in [0,1] using `sig` significant figures on the percentage.
    Keeps the ultra-small-zero threshold (100*p <= min_val) and a lower display bound:
      if pct < 10**(-sig) -> "less than {10**(-sig)}{unit}"
    """
    if _is_nan(p):
        return "NaN"

    pct = p * 100.0

    # ultra-small zero threshold (same semantics as before)
    if 100 * p <= min_val:
        return f"{zero_str}{('\u00A0' + unit) if unit else ''}"

    # lower display bound like "less than 0.01%" for sig=2
    lower_display = 10 ** (-sig)  # percent units
    if pct < lower_display:
        # format lower_display with sig significant figures but ensure we show it as decimal (not exponent)
        lower_str = _fmt_sig(lower_display, sig)
        return f"< {lower_str}{('\u00A0' + unit) if unit else ''}"

    # Otherwise format pct with sig significant figures
    s = _fmt_sig(pct, sig)
    # Special-case: if rounded percentage equals 100 => show "100" (no decimals)
    try:
        if abs(float(s) - 100.0) < 10 ** (- (sig + 1)):
            s = "100"
    except Exception:
        pass

    return f"{s}{('\u00A0' + unit) if unit else ''}"


def format_return_period_adaptive(
    rp: float,
    sig: int = 2,
    max_val: float = 1 / EPSILON,
    inf_str: str = "∞",
    unit: str = "year",
    include_unit: bool = True
) -> str:
    """
    Format a return period (years) using `sig` significant figures.
    If rp is infinite or >= max_val -> return inf_str.
    For very large values, show 'over {max_val:,}' if rp >= max_val.
    """
    if _is_nan(rp):
        return "NaN"
    if math.isinf(rp) or rp >= max_val:
        return inf_str

    rounded = _round_to_n_sigfigs(rp, sig)

    # If rounded is >= 1000, show integer grouping
    if rounded >= 1000:
        s = f"{int(round(rounded)):,}"
    else:
        s = _fmt_sig(rounded, sig, thousands_sep=False)

    if include_unit:
        plural = "s" if rounded > 1 else ""
        return f"{s}\u00A0{unit}{plural}".strip()
    
    return s


def format_ratio_adaptive(
    value: float,
    sig: int = 2,
    max_val: float = 1e5,
    min_val: float = 1e-3,
    unit: str = "time",
    include_unit: bool = True,
) -> str:
    """
    Format a ratio (e.g. PR) with `sig` significant figures.
    Keeps upper bound "over {max_val}" and lower bound "less than {min_val}".
    """
    if _is_nan(value):
        return "NaN"

    # beyond upper bound
    if value >= max_val:
        s = f"≥ {int(max_val):,}"
    # below lower bound
    elif value < min_val:
        # show 'less than {min_val}' formatted with sig figs
        min_str = _fmt_sig(min_val, sig)
        s = f"< {min_str}"
    else:
        # normal formatting: keep unit-appropriate presentation
        rounded = _round_to_n_sigfigs(value, sig)
        # if >= 1000, show grouped integer
        if rounded >= 1000:
            s = f"{int(round(rounded)):,}"
        else:
            s = _fmt_sig(rounded, sig, thousands_sep=False)

    if include_unit:
        plural = "s" if (not ("<" in s and "≥" not in s) and float(_round_to_n_sigfigs(value, sig)) > 1) else ""
        # plural calculation: if we used 'less than X' or 'over X' keep standard plural rule (value > 1)
        return f"{s}\u00A0{unit}{plural}".strip()

    return s


def format_far_adaptive(far: float, unit: str = "%") -> str:
    """
    Format FAR = 1 - 1/PR with adaptive significant figures:
    - FAR <= 99%: 2 sig figs
    - 99% < FAR < 99.9%: 3 sig figs
    - FAR >= 99.9%: 'over 99.9{unit}'
    Negative FAR returns '--'.
    """
    if _is_nan(far):
        return "NaN"
    if far < 0:
        return "--"

    p = far * 100.0

    # Lower bound
    if p < 0.01:
        return f"< 0.01{('\u00A0' + unit) if unit else ''}"

    # Upper bound
    if p >= 99.9:
        return f"≥ 99.9{('\u00A0' + unit) if unit else ''}"

    # Adaptive sig figs
    if p > 99.0:
        sig = 3
    else:
        sig = 2

    s = _fmt_sig(p, sig)
    return f"{s}{('\u00A0' + unit) if unit else ''}"


# -------- Insertions de jetons parsables dans le rendu jinja2

## Jeton à parser : [[CI:LABEL|DISPLAY]] avec :
## LABEL : La partie à afficher en tooltip
## DISPLAY : La partie à afficher in-line
 
# token = lambda disp,lo_s,hi_s: f"[[CI:Ranging from {lo_s} to {hi_s}|{disp}]]"

IPCC_format = lambda value,low,high,unit: f"**{value} *\[{low} to {high}\]* {unit}**"

# def ci_token_prob(value, lo, hi, **kwargs) -> str:
#     disp = format_prob_adaptive(value, **kwargs)
#     lo_s = format_prob_adaptive(lo, **kwargs)
#     hi_s = format_prob_adaptive(hi, **kwargs)
#     return token(disp, lo_s, hi_s)

# def ci_token_ret(value, lo, hi, **kwargs) -> str:
#     disp = format_return_period_adaptive(value, **kwargs)
#     lo_s = format_return_period_adaptive(lo, **kwargs)
#     hi_s = format_return_period_adaptive(hi, **kwargs)
#     return token(disp, lo_s, hi_s)

# def ci_token_PR(value, lo, hi, **kwargs) -> str:
#     disp = format_ratio_adaptive(value, **kwargs)
#     lo_s = format_ratio_adaptive(lo, **kwargs)
#     hi_s = format_ratio_adaptive(hi, **kwargs)
#     return token(disp, lo_s, hi_s)

# def ci_token_FAR(value, lo, hi, **kwargs) -> str:
#     disp = format_far_adaptive(value, **kwargs)
#     lo_s = format_far_adaptive(lo, **kwargs)
#     hi_s = format_far_adaptive(hi, **kwargs)
#     return token(disp, lo_s, hi_s)


def prob_with_CI(value, lo, hi, **kwargs):
    prob = format_prob_adaptive(value, unit=None, **kwargs)
    low = format_prob_adaptive(lo, unit=None, **kwargs)
    high = format_prob_adaptive(hi, unit=None, **kwargs)

    return IPCC_format(prob, low, high, "%")

def return_period_with_CI(value, lo, hi, **kwargs):
    ret = format_return_period_adaptive(value, include_unit=False, **kwargs)
    low = format_return_period_adaptive(lo, include_unit=False, **kwargs)
    high = format_return_period_adaptive(hi, include_unit=False, **kwargs)

    return IPCC_format(ret, low, high, "years")

def PR_with_CI(value, lo, hi, **kwargs):
    ratio = format_ratio_adaptive(value, include_unit=False, **kwargs)
    low = format_ratio_adaptive(lo, include_unit=False, **kwargs)
    high = format_ratio_adaptive(hi, include_unit=False, **kwargs)

    return IPCC_format(ratio, low, high, 'times')

def FAR_with_CI(value, lo, hi, **kwargs):
    far = format_far_adaptive(value, unit=None, **kwargs)
    low = format_far_adaptive(lo, unit=None, **kwargs)
    high = format_far_adaptive(hi, unit=None, **kwargs)

    return IPCC_format(far, low, high, "%")