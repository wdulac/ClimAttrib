import numpy as np
import xarray as xr
import pandas as pd

import datetime as dt

import ANKIALE as ank
# Specific imports
from ANKIALE.stats import MPeriodSmoother
from ANKIALE.stats import build_projection_matrix
from ANKIALE.stats import constraint_covar
from ANKIALE.stats.__constraint import constraint_var
from ANKIALE.cmd.__cmd_attribute import zattribute_event
from ANKIALE.__linalg import mean_cov_hpars

# Evaluate both relative path to the directory right above the main data
# directory and also to the science dir (parent to another data folder)
# 
# This mostly serves as a compatibility patch for VsCode interactive mode as
# the cwd in production should always be `app/`
import os

current_dir = os.path.basename(os.getcwd())
if current_dir == 'science':
    path_to_data_parent_dir = '../../'
    path_to_science_dir = './'
elif current_dir == 'src':
    path_to_data_parent_dir = '../'
    path_to_science_dir = './science/'
else: # Root of the app (hopefully).
    path_to_data_parent_dir = './'
    path_to_science_dir = './src/science/'

## Paramètres généraux

# Pour la contrainte Y
N_SAMPLES_COV = 100 # Tirages de covariables
SIZE_CHAIN = 100 # Nombre de valeur extraites de chaque chaine (Une chaine par tirage de covariable)
USE_STAN = True

# Pour l'attribution
N_SAMPLES_ATTRIB = 1000 # Nombre de valeurs de hpars à tirer pour l'intervalle de confiance
MODE = 'quantile'
CI = 0.05
SCENARIO = 'ssp370'

STAN_WORK_DIR = path_to_science_dir + './stan_files/'

# Pour le calendaire
# longueurs des mois en année commune (365 jours)
MONTH_LENGTHS = [31,28,31,30,31,30,31,31,30,31,30,31]
MONTH_OFFSETS = [0] + [sum(MONTH_LENGTHS[:i]) for i in range(1,12)]


def _projection_matrix(X: dict, vsize: int, smoother, constraint: dict | None = None) -> np.ndarray:

    time_size = X[next(iter(X))].time0.values.size
    return np.hstack((
        build_projection_matrix(smoother, X, constraint),
        np.zeros((time_size, vsize))
    ))


def _day_of_year_no_leap(date: dt.date) -> int:
    """Retourne le jour de l'année (1..365) en ignorant les années bissextiles."""
    return MONTH_OFFSETS[date.month-1] + date.day


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


def _load_prior(extreme_type: str, computation_method: str, start_date: dt.datetime, stop_date: dt.datetime) -> dict:

    if computation_method == 'yearmax':
        if extreme_type == 'hot':
            var = 'tmx3d'
            side = 'right'
        elif extreme_type == 'cold':
            var = 'tmn3d'
            side = 'left'
    elif computation_method == 'calendar':
        if extreme_type == 'hot':
            window = _best_window_from_range(_day_of_year_no_leap(start_date),
                                             _day_of_year_no_leap(stop_date))
            var = f'tmx3d15w_{window[0]:03d}-{window[1]:03d}'
            side = 'right'
        else:
            raise NotImplementedError
        
    clim_file = path_to_data_parent_dir + f'data/prior/{var}_CONSTRAIN_X.nc'

    clim = ank.Climatology.init_from_file(clim_file)
    # Set forcings to CMIP5 (CMIP5 XN file replaced by EBM response to CMIP6 forcings...)
    clim.cconfig.vXN = 'CMIP5'
    # Initialize CmdStan local work directory
    clim.cnslaw().init_stan(tmp=STAN_WORK_DIR, force_compile=False)
    # Matrices de projection factuel / contre-factuel
    projF, projC = clim.projection()
    # Réorganisation **temporaire** des dimensions car erreur d'indexation dans zattribute_event
    projF = projF.transpose('period', 'name', 'time', 'hpar')
    projC = projC.transpose('period', 'name', 'time', 'hpar')
    # Lissage
    mps = MPeriodSmoother(
        XN = clim.XN,
        cnames = clim.cnames,
        dpers = clim.dpers,
        spl_config = clim.cconfig.spl_config
    )

    return {
        'cnslaw': clim.cnslaw,
        'side': side,
        'time': clim.time, # Total time axis (1850 -- 2100)
        'bper': clim.bper, # Reference period for bias
        'vsize': clim.vsize,
        'projF': projF,
        'projC': projC,
        'smoother': mps,
        'hpar': clim.hpar,
        'hcov': clim.hcov
    }
    

def _load_obs(lat: float, lon: float, extreme_type: str, computation_method: str, start_date: dt.datetime, stop_date: dt.datetime) -> xr.DataArray:
    """
    Return observed covariate (GSAT timeseries) and the observed variable
    timeseries at the given grid point.
    """

    # Convert to 0 -- 360°
    lon = lon % 360

    if computation_method == 'yearmax':
        if extreme_type == 'hot':
            var_name = 'tmx3d'
            file_prefix = var_name
        elif extreme_type == 'cold':
            var_name = 'tmn3d'
            file_prefix = var_name
    elif computation_method == 'calendar':
        if extreme_type == 'hot':
            var_name = 'tmx3d15w'
            window = _best_window_from_range(_day_of_year_no_leap(start_date),
                                             _day_of_year_no_leap(stop_date))
            file_prefix = f"{var_name}_{window[0]:03d}-{window[1]:03d}"
        elif extreme_type == 'cold':
            raise NotImplementedError


    Yo_file = path_to_data_parent_dir + f'data/Yo/{var_name}/{file_prefix}_ERA5_1940-2022_1p5deg.nc'

    Yo = xr.open_dataset(Yo_file)[var_name].sel(lat=lat, lon=lon)

    # On remplace l'axe du temps par les années
    Yo = xr.DataArray(Yo.values, dims=Yo.dims,
                      coords = [Yo.time.dt.year.values] + [Yo.coords[d] for d in Yo.dims[1:]])
    
    return Yo


def attribute_event(event:dict) -> xr.Dataset:

    prior = _load_prior(event['extreme_type'], event['method'], event['start_date'], event['stop_date'])

    print('Law :', prior['cnslaw'])
    
    # Lecture du prior contraint par la covariable
    hpar_CX = prior['hpar'].sel(lat=event['lat'], lon=event['lon'] % 360, drop=True)
    hcov_CX = prior['hcov'].sel(lat=event['lat'], lon=event['lon'] % 360, drop=True)

    # Lecture des observations
    Yo = _load_obs(event['lat'], event['lon'], event['extreme_type'], event['method'], event['start_date'], event['stop_date'])

    # Calcul du biais. On pourrait utiliser la valeur stockée dans :CLIM: mais elle est légèrement différente.
    bias_arr = Yo.sel( time = slice(*[str(y) for y in prior['bper']]) ).mean('time')

    # Expression de la variable en anomalie
    Yo_anom = Yo - bias_arr

    ### Contrainte par les observations de la variable

    # Paramètres de la fonction mcmc
    iYo_anom = Yo_anom.values
    samples = np.arange(N_SAMPLES_COV)
    fake_Xo = xr.DataArray(dims=['time0'], coords=[Yo.time])
    P = _projection_matrix({'tas': fake_Xo}, prior['vsize'], prior['smoother'])
    
    # Initialisation du résultat
    ohpars = np.zeros((hpar_CX.values.size, samples.size, SIZE_CHAIN)) + np.nan
    # Boucle sur les tirages de covariable
    mcmc_args = [SIZE_CHAIN, prior['cnslaw'], USE_STAN, STAN_WORK_DIR]
    for s in samples:
        oh = constraint_var(hpar_CX, hcov_CX, iYo_anom, P, *mcmc_args)
        ohpars[:,s,:] = oh
    
    # calcul des paramètres de la distribution des tirages MCMC
    hpar_CXCB, hcov_CXCB = mean_cov_hpars(ohpars)

    ### Attribution de l'évènement

    # Paramètres de la fonction d'attribution
    ihpar = hpar_CXCB[np.newaxis, np.newaxis, :] # (lat, lon, hpar).
    ihcov = hcov_CXCB[np.newaxis, np.newaxis, :, :] # (lat, lon, hpar0, hpar1)
    bias = bias_arr.values[np.newaxis, np.newaxis] # (lat, lon)
    To = event['intensity'] - bias # idem
    iprojF = prior['projF'].values
    iprojC = prior['projC'].values
    idx_event = int(np.argwhere(prior['time'] == event['date'].year).ravel())

    # Calcul des statistiques de l'évènement
    out_CXCB = zattribute_event(ihpar, ihcov, bias, To, iprojF, iprojC, idx_event, prior['cnslaw'], prior['side'], MODE, N_SAMPLES_ATTRIB, CI)
    keys = ["pF","pC","RF","RC","IF","IC","dI","PR"]
    out_CXCB  = { key : out_CXCB[ikey][0,:,:,:] for ikey,key in enumerate(keys) } # Sort en (1, period, time, quantile)

    # Conversion en xr.Dataset
    modes = np.array(["QL","BE","QU"])
    data_arrays = []
    
    for key, value in out_CXCB.items():
        da = xr.DataArray(
            value,
            coords=[['ssp370', 'ssp585'], prior['time'], modes],
            dims=['scenario', 'time', 'quantile'],
            name=key
        )
        data_arrays.append(da)

    dataset = xr.Dataset({da.name: da for da in data_arrays})

    dataset.attrs['time'] = int(event['date'].year)

    return dataset.sel(scenario=SCENARIO)