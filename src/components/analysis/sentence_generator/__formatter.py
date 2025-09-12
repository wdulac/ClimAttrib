import math

EPSILON = 10*__import__("sys").float_info.epsilon

# ---------- utilitaires ----------
def _is_nan(x): return x is None or (isinstance(x, float) and math.isnan(x))

def _sig_round(x: float, sig: int) -> float:
    if x == 0 or _is_nan(x):
        return x
    return round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)

def _format_int_or_float(x: float, max_decimals: int = 2) -> str:
    # "57", "57.1", "0.034"
    if _is_nan(x):
        return "NaN"
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x))}"
    return f"{x:.{max_decimals}f}".rstrip("0").rstrip(".")

# ---------- Probabilité (fraction → %) ----------
def format_prob_adaptive(p: float, fp: int = 2, min_pct: float = 0.01, zero_str="0", unit="%") -> str:
    """p en [0,1]. Affiche en %, précision selon l’ordre de grandeur."""
    if _is_nan(p):
        return "NaN"
    pct = p * 100.0

    # bornes
    if pct <= 0:
        return f"{zero_str}{(' ' + unit) if unit else ''}"
    if pct >= 99.995:  # 100% propre
        return f"100{unit and ' ' + unit or ''}"

    # très petit
    if pct < min_pct:
        return f"< {min_pct}{unit and ' ' + unit or ''}"

    # magnitude → décimales
    if pct < 0.1:
        s = f"{pct:.3f}"
    elif pct < 1:
        s = f"{pct:.2f}"
    elif pct < 10:
        s = f"{pct:.2f}"
    elif pct < 100:
        s = f"{pct:.1f}"
    else:
        s = f"{pct:.0f}"

    s = s.rstrip("0").rstrip(".")
    return f"{s}{unit and ' ' + unit or ''}"

# ---------- Durée de retour (années) ----------
def format_return_period_adaptive(rp: float, max_val: float = 1/EPSILON,
                                  inf_str="infinity", unit="year") -> str:
    if _is_nan(rp):
        return "NaN"
    if math.isinf(rp) or rp >= max_val:
        return inf_str

    # pas variable en fonction de l’échelle
    if rp < 20:
        s = f"{rp:.1f}"
    elif rp < 100:
        s = f"{round(rp)}"
    elif rp < 1_000:
        s = f"{int(round(rp / 5) * 5)}"
    elif rp < 1_000_000:
        s = f"{rp/1_000:.1f}k"
    elif rp < 1_000_000_000:
        s = f"{rp/1_000_000:.1f}M"
    else:
        s = f"{rp/1_000_000_000:.1f}G"

    plural = "s" if rp > 1.05 else ""  # seuil léger pour éviter 1.0 → "years"
    return f"{s} {unit}{plural}".strip()

# ---------- Ratio PR (× plus probable) ----------
def format_ratio_adaptive(r: float, small_cut=1.5) -> str:
    if _is_nan(r):
        return "NaN"
    if r < small_cut:
        # autour de 1 → 2 décimales
        return _format_int_or_float(r, max_decimals=2)
    elif r < 10:
        return _format_int_or_float(r, max_decimals=1)
    elif r < 100:
        return f"{int(round(r))}"
    elif r < 10_000:
        # pas de 5
        return f"{int(round(r/5)*5)}"
    else:
        # notation abrégée
        if r < 1_000_000:
            return f"{r/1_000:.1f}k"
        elif r < 1_000_000_000:
            return f"{r/1_000_000:.1f}M"
        else:
            return f"{r/1_000_000_000:.1f}G"

# ---------- FAR ----------
def format_far_adaptive(far: float, min_pct=0.1, unit="%") -> str:
    # FAR exprimée en fraction [0,1] → %
    if _is_nan(far):
        return "NaN"
    pct = far * 100.0
    if pct < 0:
        return "0" + (f" {unit}" if unit else "")
    if pct < min_pct:
        return f"< {min_pct}{unit and ' ' + unit or ''}"
    if pct > 99.95:
        return f"~100{unit and ' ' + unit or ''}"
    # magnitude
    if pct < 1:
        s = f"{pct:.2f}"
    elif pct < 10:
        s = f"{pct:.1f}"
    else:
        s = f"{pct:.1f}"
    s = s.rstrip("0").rstrip(".")
    return f"{s}{unit and ' ' + unit or ''}"