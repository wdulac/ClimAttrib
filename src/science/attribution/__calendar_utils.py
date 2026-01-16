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