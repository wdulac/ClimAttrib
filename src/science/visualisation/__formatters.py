import numpy as np
import math
import sys

EPSILON = 10*sys.float_info.epsilon

def _round_to_n_sigfigs(x: float, n: int = 2) -> float:
    """Round x to n significant figures. Works for x > 0 and x < 0, returns 0.0 for x == 0."""
    if x == 0 or x is None or np.isnan(x):
        return 0.0
    sign = 1 if x > 0 else -1
    x_abs = abs(x)
    exponent = math.floor(math.log10(x_abs))
    factor = 10 ** (exponent - (n - 1))
    return sign * round(x / factor) * factor


def _fmt_sig_plot(x: float, sig: int = 2) -> str:
    """
    Version allégée pour Plotly :
    - pas de séparateur de milliers
    - pas de locale
    - pas d'espaces insécables
    """
    if np.isnan(x):
        return "NaN"
    if x == 0:
        return "0"

    rounded = _round_to_n_sigfigs(x, sig)
    mag = abs(rounded)

    # Si ~entier, on retourne un entier
    if mag >= 1 and abs(rounded - round(rounded)) < 1e-12:
        return str(int(round(rounded)))

    # sinon : décimales selon les sig figs
    digits_before = math.floor(math.log10(mag)) + 1 if mag >= 1 else 0
    decimals = max(0, sig - digits_before)
    s = f"{rounded:.{decimals}f}"

    # trim des zéros
    if "." in s:
        s = s.rstrip("0").rstrip(".")

    return s


def _safe_prob(value, fp=2, min_val=EPSILON, zero_str="0", unit="%"):
    """Probabilité p∈[0,1] -> pourcentage à fp chiffres significatifs (sur le %)."""
    if np.isnan(value):
        return "NaN"

    sig = fp  # on réutilise fp comme nb de chiffres significatifs sur le %
    pct = value * 100.0

    # ultra-petit -> zéro
    if 100 * value <= min_val:
        return f"{zero_str} {unit}" if unit else zero_str

    # borne basse : "< 0.01%" pour sig=2
    lower_display = 10 ** (-sig)
    if pct < lower_display:
        lower_str = _fmt_sig_plot(lower_display, sig)
        return f"< {lower_str}{unit if unit else ''}"

    # sinon : % avec sig chiffres significatifs
    s = _fmt_sig_plot(pct, sig)

    # si ça tombe sur 100 pile, on force "100"
    try:
        if abs(float(s) - 100.0) < 10 ** (-(sig + 1)):
            s = "100"
    except Exception:
        pass

    return f"{s}{unit if unit else ''}"


def _safe_ret(value, max_val=1/EPSILON, inf_str="infinity", unit="year"):
    """Durée de retour (années) avec 2 chiffres significatifs + suffixes k/M/G."""
    if np.isnan(value):
        return "NaN"
    if np.isinf(value) or value >= max_val:
        return inf_str

    v = float(value)

    # Choix de l'échelle pour k / M / G
    if v < 1_000:
        # valeurs < 1000 : nombre brut à 2 chiffres significatifs
        s_val = _fmt_sig_plot(v, 2)
        suffix = ""
    elif v < 1_000_000:
        s_val = _fmt_sig_plot(v / 1_000.0, 2)
        suffix = "k"
    elif v < 1_000_000_000:
        s_val = _fmt_sig_plot(v / 1_000_000.0, 2)
        suffix = "M"
    else:
        s_val = _fmt_sig_plot(v / 1_000_000_000.0, 2)
        suffix = "G"

    s = f"{s_val}{suffix}"
    if unit:
        plural = (unit + "s") if round(v, 1) > 1 else unit
    return f"{s} {plural}" if unit else s

        
def _safe_PR(value, max_val=1e5, min_val=1e-3):
    """PR avec 2 chiffres significatifs + bornes min/max numériques."""
    if np.isnan(value):
        return "NaN"

    v = float(value)

    # borne haute : "> max_val"
    if v >= max_val:
        # on garde l'affichage avec espace comme avant
        return f"> {int(max_val):,}".replace(",", " ")

    # borne basse : "< min_val"
    if v < min_val:
        min_str = _fmt_sig_plot(min_val, 2)
        return f"< {min_str}"

    # entre les bornes : 2 chiffres significatifs
    rounded = _round_to_n_sigfigs(v, 2)

    # pour des valeurs très grandes, on peut éventuellement regrouper,
    # mais ici on reste simple (pas de k/M/G pour PR)
    s = _fmt_sig_plot(rounded, 2)
    return s


def _safe_FAR(value, unit="%"):
    """
    FAR en %, style numérique :
    - FAR < 0.01%     -> '< 0.01%'
    - 0.01% <= FAR <= 99%  -> 2 sig figs
    - 99% < FAR < 99.9%    -> 3 sig figs
    - FAR >= 99.9%         -> '> 99.9%'
    
    Args:
        value: FAR value (0-1)
        unit: Unit suffix (default '%'). Set to None to omit unit.
    """
    if np.isnan(value):
        return "NaN"
    if value < 0:
        return "--"

    p = float(value) * 100.0

    # borne basse
    if p < 0.01:
        return f"< 0.01{unit if unit else ''}"

    # borne haute
    if p >= 99.9:
        return f"> 99.9{unit if unit else ''}"

    # entre 99 et 99.9 : 3 chiffres significatifs
    if p > 99.0:
        sig = 3
    else:
        sig = 2

    s = _fmt_sig_plot(p, sig)
    return f"{s}{unit if unit else ''}"


def _safe_intensity(value, unit='°C'):

    if np.isnan(value):
        return "NaN"
    
    return f"{value:.1f}{unit if unit else ''}"


def _safe_intensity_change(value, unit='°C'):

    if np.isnan(value):
        return "NaN"
    
    return f"{value:+.1f}{unit if unit else ''}"


def _annual_series_hover(event=False, return_level=False, p=None):
    if event:
        return (
            "<b>User event</b>: %{y:.1f} °C"
            "<extra></extra>"
        )

    if return_level:
        if p:
            pre = int(1/p)
            return (
                f"<b>{pre}-year return level</b>: %{{y:.1f}} °C"
                "<extra></extra>"
            )
        else:
            return (
                "<b>Return level</b>: %{y:.1f} °C"
                "<extra></extra>"
            )


    return (
        "<b>Annual maximum</b>: %{y:.1f} °C"
        "<extra></extra>"
    )


def _daily_temperature_hover(ref=False):

    if ref:
        return (
            "<b>1991 — 2020 median</b>: %{y:.1f} °C"
            "<extra></extra>"
        )
    else:
        return (
            "<b>%{customdata} temperature</b>: %{y:.1f} °C"
            "<extra></extra>"
        )