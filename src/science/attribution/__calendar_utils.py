"""
Calendar utilities for the attribution algorithm.

Handles the day-of-year (DOY) convention used throughout the science layer: DOY 60
is permanently reserved for February 29, so non-leap years skip DOY 60 and DOY 366
is valid for all years (it maps to December 31 in non-leap years after a shift).

- ``_datetime_to_doy(date)`` — converts a ``datetime`` to a DOY in [1, 366] using
  the leap-year convention above.
- ``_doy_to_datetime(doy, year)`` — inverse conversion; raises ``ValueError`` for
  DOY 60 in a non-leap year.
- ``_best_window_from_range(day_start, day_end, n_days, win_len, step)`` — given an
  event date range (as DOY values, possibly wrapping across year boundaries), finds
  the 15-day comparison window (aligned to a 5-day grid) that best centres the
  event. Returns the window as ``(start_doy, end_doy)``. Used to select the
  matching prior file for the calendar computation method.
"""

import datetime as dt
import calendar


def _datetime_to_doy(date: dt.datetime) -> int:
    """
    date : dt.datetime (jour-mois-année)
    
    Convertit une date au format 'jour-mois-année' en jour de l'année
    entre 0 et 365.
    """
    doy = date.timetuple().tm_yday
    if not calendar.isleap(date.year):
        if date.month >= 3:
            doy += 1
    return doy


def _doy_to_datetime(doy: int, year: int) -> dt.datetime:
    """
    Inverse de _datetime_to_doy.

    Parameters
    ----------
    doy : int
        Day of year in [1, 366], avec 60 réservé au 29/02
        même pour les années non bissextiles.
    year : int
        Année de référence.

    Returns
    -------
    dt.datetime
        Date correspondante.
    """

    doy = int(doy)

    if doy < 1 or doy > 366:
        raise ValueError("doy must be between 1 and 366")

    # En année non bissextile, on saute le 29 février
    if not calendar.isleap(year):
        if doy == 60:
            raise ValueError("doy=60 (29 Feb) is invalid for a non-leap year")
        if doy > 60:
            doy -= 1

    return dt.datetime(year, 1, 1) + dt.timedelta(days=doy - 1)


def _best_window_from_range(day_start, day_end, n_days=365, win_len=15, step=5):
    """
    day_start, day_end : jours de l'année (1-based), inclusifs.
        - Peut traverser le 31 déc → 1 jan (ex: 361..2).
    n_days : 365 ou 366.
    win_len : longueur de la fenêtre (par défaut 15).
    step : pas entre débuts de fenêtre (par défaut 5).
    
    Retourne (s, e) : bornes 1-based de la fenêtre [s, e] qui
    (1) contient l'épisode et (2) centre au mieux l'épisode.
    """
    a = int(day_start)
    b = int(day_end)

    # Déplier l'intervalle épisode sur une droite (gestion wrap)
    # Exemple: a=361, b=2 (wrap) → b_unwrapped = 2 + 365 = 367
    b_unwrapped = b if b >= a else b + n_days
    d = b_unwrapped - a + 1  # durée de l'épisode

    if d > win_len:
        raise ValueError(f"Épisode de durée {d} > fenêtre {win_len} : impossible de contenir.")

    # Centre de l'épisode dans l'espace déplié
    cb = a + (d - 1) / 2.0

    # Bornes d'inclusion admissibles pour le début de fenêtre (dans l'espace déplié)
    # Il faut s <= a et a+d-1 <= s+win_len-1  ⇒  s >= a + d - win_len
    lo = a + d - win_len
    hi = a

    # Génère les starts ≡ 1 (mod step) dans [lo, hi] (déplié),
    # puis replie modulo n_days pour renvoyer en 1..n_days
    def starts_in(lo, hi):
        res = []
        # intervalle non-wrap car on est en "déplié"
        r = (lo - 1) % step
        first = lo if r == 0 else lo + (step - r)
        s = first
        while s <= hi:
            res.append(s)
            s += step
        return res

    cand_unwrapped = starts_in(lo, hi)
    if not cand_unwrapped:
        raise ValueError("Aucun début de fenêtre admissible (vérifier paramètres).")

    # Choisir le s dont le centre de fenêtre est le plus proche du centre épisode
    def dist(s):
        cw = s + (win_len - 1) / 2.0
        return abs(cw - cb)

    s_best_unwrapped = min(cand_unwrapped, key=dist)

    # Replier le résultat dans [1, n_days]
    s_best = ((s_best_unwrapped - 1) % n_days) + 1
    e_best = ((s_best + win_len - 1 - 1) % n_days) + 1
    return s_best, e_best