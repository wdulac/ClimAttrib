import math

EPSILON = 10*__import__("sys").float_info.epsilon

# ---------- utilitaires ----------
def _is_nan(x): return x is None or (isinstance(x, float) and math.isnan(x))


# -------- Probabilité (p∈[0,1]) — mêmes règles que _safe_prob --------
def format_prob_adaptive(p: float, fp: int = 2, min_val: float = EPSILON,
                         zero_str="0", unit="%") -> str:
    if _is_nan(p):
        return "NaN"
    pct = p * 100.0

    # 0 (seuil ultra-faible) — même test que _safe_prob (100*p <= min_val)
    if 100 * p <= min_val:
        return f"{zero_str}{('\u00A0' + unit) if unit else ''}"

    # borne "< 10^-fp"
    if 100 * p < pow(10, -fp):
        return f"less than {pow(10, -fp)}{('\u00A0' + unit) if unit else ''}"

    # 100% propre si round(pct, 2) == 100
    if round(pct, 2) == 100:
        s = format(pct, ".0f")
    else:
        s = format(pct, f".{fp}f")

    return f"{s}{('\u00A0' + unit) if unit else ''}"

# -------- Durée de retour — mêmes règles que _safe_ret --------
def format_return_period_adaptive(rp: float, max_val: float = 1/EPSILON,
                                  inf_str="infinity", unit="year") -> str:
    if _is_nan(rp):
        return "NaN"
    if math.isinf(rp) or rp >= max_val:
        return inf_str

    # paliers identiques à _safe_ret._format_years
    if rp < 20:
        s = f"{rp:.1f}"
    elif rp < 100:
        s = f"{round(rp)}"
    elif rp < 1_000:
        s = f"{int(round(rp/5) * 5)}"
    elif rp < 1_000_000:
        s = f"{int(round(rp/100) * 100):n}"
        # s = f"{rp/1_000:.1f} thousand"
    elif rp < 1_000_000_000:
        s = f"{int(round(rp/100_000) * 100_000):n}"
        # s = f"{rp/1_000_000:.1f} million"
    else:
        s = f"{int(round(rp/100_000_000) * 100_000_000):n}"
        # s = f"{rp/1_000_000_000:.1f} billion"

    # Pluriel identique (round(value, 1) > 1)
    plural = "s" if round(rp, 1) > 1 else ""
    return f"{s}\u00A0{unit}{plural}".strip()

# -------- Ratio PR — mêmes règles que _safe_PR --------
def format_ratio_adaptive(
    value: float,
    max_val: float = 1e5,
    min_val: float = 1e-3,
    unit: str = "time",
    include_unit: bool = True,
) -> str:
    if _is_nan(value):
        return "NaN"

    # utilitaire pour nettoyer "1.50" -> "1.5", "2.00" -> "2"
    def _trim(x: str) -> str:
        return x.rstrip("0").rstrip(".") if "." in x else x

    # 1) cas "au-delà de la borne"
    if value >= max_val:
        s = f"over {int(max_val):n}"

    # 2) ratios > 1
    elif value > 1:
        if value < 10:
            s = _trim(f"{value:.2f}")
        elif value < 20:
            s = _trim(f"{value:.1f}")
        elif value < 100:
            s = str(round(value))
        elif value < 1_000:
            s = str(round(value / 5) * 5)
        elif value < 10_000:
            s = str(round(value / 50) * 50)
        else:
            s = str(round(value / 500) * 500)

    # 3) ratios <= 1
    else:
        if value >= 0.01:
            s = _trim(f"{value:.2f}")
        elif value < min_val:
            s = f"less than {min_val:.3f}".rstrip("0").rstrip(".")
        else:
            s = _trim(f"{value:.3f}")

    if include_unit:
        plural = "s" if round(value, 1) > 1 else ""
        return f"{s}\u00A0{unit}{plural}".strip()

    return s

# -------- FAR — mêmes règles que _safe_FAR --------
def format_far_adaptive(far: float) -> str:
    if _is_nan(far):
        return "NaN"
    if far < 0:
        return "--"
    p = far * 100.0
    if round(p, 2) > 99.99:
        return "over 99.99\u00A0%"
    else:
        return f"{p:.2f}\u00A0%"

# -------- Insertions de jetons parsables dans le rendu jinja2

## Jeton à parser : [[CI:LABEL|DISPLAY]] avec :
## LABEL : La partie à afficher en tooltip
## DISPLAY : La partie à afficher in-line
 
token = lambda disp,lo_s,hi_s: f"[[CI:Ranging from {lo_s} to {hi_s}|{disp}]]"

def ci_token_prob(value, lo, hi, **kwargs) -> str:
    disp = format_prob_adaptive(value, **kwargs)
    lo_s = format_prob_adaptive(lo, **kwargs)
    hi_s = format_prob_adaptive(hi, **kwargs)
    return token(disp, lo_s, hi_s)

def ci_token_ret(value, lo, hi, **kwargs) -> str:
    disp = format_return_period_adaptive(value, **kwargs)
    lo_s = format_return_period_adaptive(lo, **kwargs)
    hi_s = format_return_period_adaptive(hi, **kwargs)
    return token(disp, lo_s, hi_s)

def ci_token_PR(value, lo, hi, **kwargs) -> str:
    disp = format_ratio_adaptive(value, **kwargs)
    lo_s = format_ratio_adaptive(lo, **kwargs)
    hi_s = format_ratio_adaptive(hi, **kwargs)
    return token(disp, lo_s, hi_s)

def ci_token_FAR(value, lo, hi, **kwargs) -> str:
    disp = format_far_adaptive(value, **kwargs)
    lo_s = format_far_adaptive(lo, **kwargs)
    hi_s = format_far_adaptive(hi, **kwargs)
    return token(disp, lo_s, hi_s)