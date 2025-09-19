import math

EPSILON = 10*__import__("sys").float_info.epsilon

# ---------- utilitaires ----------
def _is_nan(x): return x is None or (isinstance(x, float) and math.isnan(x))

def _round_sig(x: float, sig: int) -> float:
    if _is_nan(x) or x == 0:
        return x
    return round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)

def _rel_width(center: float, lo: float, hi: float) -> float:
    if _is_nan(center) or _is_nan(lo) or _is_nan(hi):
        return math.inf
    span = abs(hi - lo)
    denom = abs(center) if abs(center) > EPSILON else (abs(hi) if abs(hi) > EPSILON else 1.0)
    return span / denom

def _sig_from_rel(rel: float, min_sig=1, max_sig=3) -> int:
    # Relativement large -> peu de sig figs; étroit -> plus de sig figs (capé)
    if rel >= 1.0: return 1
    if rel >= 0.5: return 2
    if rel >= 0.2: return 3
    return max_sig

def _decimals_from_rel_pct(rel: float) -> int:
    # Nombre de décimales en % (lisible presse)
    if rel >= 1.0: return 0
    if rel >= 0.5: return 1
    return 2  # rel < 0.5

def _format_int_or_float(x: float, max_decimals: int = 2) -> str:
    # "57", "57.1", "0.034"
    if _is_nan(x):
        return "NaN"
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x))}"
    return f"{x:.{max_decimals}f}".rstrip("0").rstrip(".")

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
def format_ratio_adaptive(value: float, max_val: float = 1e5, min_val: float = 1e-3) -> str:
    if _is_nan(value):
        return "NaN"

    if value >= max_val:
        # même rendu que _safe_PR : '> 100 000' (espaces comme séparateur)
        return f"> {int(max_val):,}".replace(",", " ")

    if value > 1:
        if value < 10:
            return f"{value:.2f}"
        elif value < 20:
            return f"{value:.1f}"
        elif value < 100:
            return str(round(value))
        elif value < 1_000:
            return str(round(value / 5) * 5)
        elif value < 10_000:
            return str(round(value / 50) * 50)
        else:
            return str(round(value / 500) * 500)
    else:
        if value >= 0.01:
            return f"{value:.2f}"
        elif value < min_val:
            return f"< {min_val:.3f}"
        else:
            return f"{value:.3f}"

# -------- FAR — mêmes règles que _safe_FAR --------
def format_far_adaptive(far: float) -> str:
    if _is_nan(far):
        return "NaN"
    if far < 0:
        return "--"
    p = far * 100.0
    if round(p, 2) > 99.99:
        return "more than 99.99\u00A0%"
    else:
        return f"{p:.2f}\u00A0%"

# ---------- Probabilité (fraction → %, CI-aware) ----------
def format_prob_ci(p: float, lo: float, hi: float, min_pct: float = 0.01, unit: str = "%") -> str:
    if _is_nan(p): return "NaN"
    pct = p * 100.0
    if pct <= 0: return f"0{unit and ' ' + unit or ''}"
    if pct >= 99.995: return f"100{unit and ' ' + unit or ''}"
    if pct < min_pct: return f"< {min_pct}{unit and ' ' + unit or ''}"

    rel = _rel_width(p, lo, hi)
    d = _decimals_from_rel_pct(rel)
    s = f"{pct:.{d}f}".rstrip("0").rstrip(".")
    return f"{s}{unit and ' ' + unit or ''}"

# ---------- Durée de retour (années, CI-aware via sig figs) ----------
def format_return_period_ci(rp: float, lo: float, hi: float, unit: str = "year", inf_str="infinity") -> str:
    if _is_nan(rp): return "NaN"
    if math.isinf(rp): return inf_str
    rel = _rel_width(rp, lo, hi)
    sig = _sig_from_rel(rel)  # 1–3 sig figs
    val = _round_sig(rp, sig)

    # Affichage lisible (k/M/G au besoin)
    a = abs(val)
    if a < 1000:
        out = f"{val:.0f}" if a >= 20 else f"{val:.1f}"
    elif a < 1_000_000:
        out = f"{val/1_000:.1f}k"
    elif a < 1_000_000_000:
        out = f"{val/1_000_000:.1f}M"
    else:
        out = f"{val/1_000_000_000:.1f}G"

    plural = "s" if rp > 1.05 else ""
    return f"{out} {unit}{plural}".strip()

# ---------- Ratio PR (× plus probable, CI-aware via sig figs) ----------
def format_PR_ci(r: float, lo: float, hi: float) -> str:
    if _is_nan(r):
        return "NaN"
    if r <= 0:
        return "0"

    rel = _rel_width(r, lo, hi)
    sig = _sig_from_rel(rel)  # 1–3 sig figs en fonction de la largeur relative

    # Ne pas “écraser” 1.x à 1 : garder au moins 2 sig figs autour de 1
    if 0.5 < r < 0.95 or 1.05 < r < 2.0:
        sig = max(sig, 2)

    val = _round_sig(r, sig)
    a = abs(val)

    if a < 10:
        # Toujours au moins une décimale < 10
        s = f"{val:.1f}".rstrip("0").rstrip(".")
        # Sécurité: si val ∈ (1,2) et que le strip a tout enlevé, remet 1 décimale
        if 1.0 < val < 2.0 and "." not in s:
            s = f"{val:.1f}"
    elif a < 100:
        s = f"{int(round(val))}"
    elif a < 10_000:
        s = f"{int(round(val/5)*5)}"
    elif a < 1_000_000:
        s = f"{val/1_000:.1f}k"
    elif a < 1_000_000_000:
        s = f"{val/1_000_000:.1f}M"
    else:
        s = f"{val/1_000_000_000:.1f}G"

    return s

# ---------- FAR (fraction → %, CI-aware) ----------
def format_FAR_ci(far: float, lo: float, hi: float, unit: str = "%") -> str:
    if _is_nan(far): return "NaN"
    # FAR peut être <0 si PR<1 → clamp à 0 pour l’affichage presse
    far = max(far, 0.0)
    pct = far * 100.0
    if pct >= 99.95: return f"~100{unit and ' ' + unit or ''}"

    rel = _rel_width(far, lo, hi)
    d = _decimals_from_rel_pct(rel)  # 0/1/2 décimales max
    if pct < 0.1: d = max(d, 2)
    s = f"{pct:.{d}f}".rstrip("0").rstrip(".")
    return f"{s}{unit and ' ' + unit or ''}"