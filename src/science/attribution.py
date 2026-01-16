import numpy as np
import xarray as xr
import pandas as pd
import sys
import os

import datetime as dt
import calendar

import ANKIALE as ank
# Specific imports
from ANKIALE.stats import MPeriodSmoother
from ANKIALE.stats.__constraint import constraint_var

from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Sequence, Tuple

from utils.paths import DATA, SRC

## Paramètres généraux

# Pour la contrainte Y
N_SAMPLES_COV = 100 # Tirages de covariables
SIZE_CHAIN = 100 # Nombre de valeur extraites de chaque chaine (Une chaine par tirage de covariable)
METHOD_CONSTRAINT = {'GMST': 'full'}
USE_STAN = True
MASTER_SEED = int(os.getenv('MASTER_SEED', 123456))


# Pour l'attribution
N_SAMPLES_ATTRIB = 1000 # Nombre de valeurs de hpars à tirer pour l'intervalle de confiance
MODE = 'quantile'
CI = 0.05
SCENARIO = 'ssp370'

STAN_WORK_DIR =  SRC / 'science/stan_files/'


def _datetime_to_doy(date: dt.datetime) -> int:
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


def _load_prior(extreme_type: str, computation_method: str, start_date: dt.datetime, stop_date: dt.datetime, duration: int) -> dict:

    if computation_method == 'yearmax':
        if extreme_type == 'hot':
            var = f'tmx{duration}d'
            side = 'right'
        elif extreme_type == 'cold':
            var = f'tmn{duration}d'
            side = 'left'
    elif computation_method == 'calendar':
        if duration == 3:
            if extreme_type == 'hot':
                window = _best_window_from_range(_datetime_to_doy(start_date),
                                                _datetime_to_doy(stop_date))
                var = f'tmx3d15w_{window[0]:03d}-{window[1]:03d}'
                side = 'right'
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError
        
    clim_file =  DATA / f'prior/{var}_CONSTRAIN_X.nc'

    clim = ank.Climatology.init_from_file(clim_file)
    # Set forcings to CMIP5 (CMIP5 XN file replaced by EBM response to CMIP6 forcings...)
    clim.cconfig.vXN = 'CMIP5'
    # Initialize CmdStan local work directory
    clim.cnslaw().init_stan(tmp=STAN_WORK_DIR, force_compile=False)
    # Matrices de projection factuel / contre-factuel
    projF, projC = clim.projection()
    nper = projF.shape[1]
    # Lissage
    mps = MPeriodSmoother(
        XN = clim.XN,
        total_dof=clim.cconfig.total_dof,
        n_spl_basis = clim.cconfig.nknot,
        degree = clim.cconfig.degree
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
        'n_scenario': nper,
        'hpar': clim.hpar,
        'hcov': clim.hcov
    }
    

def _load_obs(lat: float, lon: float, extreme_type: str, computation_method: str,
              start_date: dt.datetime, stop_date: dt.datetime,
              duration: int) -> xr.DataArray:
    """
    Return observed covariate (GSAT timeseries) and the observed variable
    timeseries at the given grid point.
    """

    # Convert to 0 -- 360°
    lon = lon % 360

    if computation_method == 'yearmax':
        if extreme_type == 'hot':
            var_name = f'tmx{duration}d'
            file_prefix = var_name
        elif extreme_type == 'cold':
            var_name = f'tmn{duration}d'
            file_prefix = var_name
    elif computation_method == 'calendar':
        if extreme_type == 'hot':
            var_name = 'tmx3d15w'
            window = _best_window_from_range(_datetime_to_doy(start_date),
                                             _datetime_to_doy(stop_date))
            file_prefix = f"{var_name}_{window[0]:03d}-{window[1]:03d}"
        elif extreme_type == 'cold':
            raise NotImplementedError


    Yo_file = DATA / f'Yo/{var_name}/{file_prefix}_ERA5_1940-2024_1p5deg.nc'

    Yo = xr.open_dataset(Yo_file)[var_name].sel(lat=lat, lon=lon)

    # On remplace l'axe du temps par les années
    Yo = xr.DataArray(Yo.values, dims=Yo.dims,
                      coords = [Yo.time.dt.year.values] + [Yo.coords[d] for d in Yo.dims[1:]])
    
    return Yo


def _worker_block(sample_chunk: Sequence[int],
                  task_seeds: Sequence[int],
                  stan_seeds: Sequence[int],
                  hpar_CX: np.ndarray,
                  hcov_CX: np.ndarray,
                  iYo_anom: np.ndarray,
                  P: np.ndarray,
                  SIZE_CHAIN: int,
                  cnslaw,
                  USE_STAN: bool,
                  STAN_WORK_DIR: str,
                  n_scenario: int) -> Tuple[Sequence[int], np.ndarray]:
    """
    Exécuté dans chaque process : calcule les oh pour chaque sample du bloc,
    et renvoie (sample_chunk, block_hpars).
    block_hpars shape = (len(sample_chunk)*SIZE_CHAIN, n_scenario, hpar_dim)
    """
    
    hpar_dim = hpar_CX.size
    block = np.zeros((len(sample_chunk) * SIZE_CHAIN, n_scenario, hpar_dim)) + np.nan

    for i, s in enumerate(sample_chunk):
        local_rng = np.random.default_rng(task_seeds[s])
        # Application du MCMC
        oh = constraint_var(hpar_CX, hcov_CX, iYo_anom, P, SIZE_CHAIN, cnslaw, USE_STAN, stan_seeds[s], STAN_WORK_DIR, rng=local_rng)
        # On réplique la sortie du MCMC pour tous les scénarios
        block[i*SIZE_CHAIN:(i+1)*SIZE_CHAIN, :, :] = np.tile(oh.T[:, np.newaxis, :], (1, n_scenario, 1))

    return sample_chunk, block


def attribute_event(event:dict, save_to_disk=False, n_process=4) -> xr.Dataset:

    # Lecture du prior contraint par la covariable
    prior = _load_prior(event['extreme_type'], event['method'], event['start_date'], event['stop_date'], event['duration'])
    hpar_CX = prior['hpar'].sel(lat=event['lat'], lon=event['lon'] % 360, drop=True)
    hcov_CX = prior['hcov'].sel(lat=event['lat'], lon=event['lon'] % 360, drop=True)

    # Lecture des observations
    Yo = _load_obs(event['lat'], event['lon'],
                   event['extreme_type'], event['method'],
                   event['start_date'], event['stop_date'],
                   event['duration'])
    
    # Append today's observation if it constitutes a new all-time extreme
    is_new_extreme = (
        (event['extreme_type'] == 'hot'  and event['intensity'] > Yo.max()) or
        (event['extreme_type'] == 'cold' and event['intensity'] < Yo.min())
    )
    if is_new_extreme:
        # Assumption: Yo timeseries stops at year n-1 from today
        today_year = dt.date.today().year
        new_value = xr.DataArray(event['intensity'], coords={'time': today_year})
        Yo = xr.concat([Yo, new_value], dim='time')

    # Calcul du biais.
    bias = float(Yo.sel( time = slice(*[str(y) for y in prior['bper']]) ).mean('time'))

    # Expression de la variable en anomalie
    Yo_anom = Yo - bias

    ### Contrainte par les observations de la variable

    # Paramètres d'entrée pour la contrainte Y
    iYo_anom = Yo_anom.values
    samples = np.arange(N_SAMPLES_COV)

    # Matrice de projection pour les observations
    P = prior['smoother'].obs_projection(mix_periods=METHOD_CONSTRAINT, time={'GMST':Yo.time.values})
    vP = np.zeros((P.shape[0], prior['vsize']))
    P = np.hstack((P, vP))

    n_scenario = prior['n_scenario']
    
    ## Parallélisation de la contrainte Y en répartissant les samples sur n_process

    # Gestion des seed pour stan
    rng = np.random.default_rng(MASTER_SEED)
    stan_seeds = rng.integers(
        low=0,
        high=2**32 - 1,
        size=N_SAMPLES_COV,
        dtype=np.uint32
    )

    # Gestion des seeds pour initialiser d'autres np.random.Generator
    tasks_seeds = rng.integers(
        0, 2**32 - 1, size=N_SAMPLES_COV, dtype=np.uint32
    )

    # Découpe la liste des samples en chunks approximativement égaux
    raw_chunks = np.array_split(np.array(samples), n_process)
    chunks = [c.tolist() for c in raw_chunks if len(c) > 0]

    # Allocation du résultat
    hpars = np.zeros((N_SAMPLES_COV * SIZE_CHAIN, n_scenario, hpar_CX.size)) + np.nan

    # Lance un processus par chunk
    with ProcessPoolExecutor(max_workers=len(chunks)) as ex:
        futures = [ex.submit(_worker_block, chunk, tasks_seeds, stan_seeds, hpar_CX, hcov_CX, iYo_anom, P,
                             SIZE_CHAIN, prior['cnslaw'], USE_STAN, STAN_WORK_DIR,n_scenario)
                   for chunk in chunks]

        for future in as_completed(futures):
            chunk, block = future.result()
            for i, s in enumerate(chunk):
                hpars[s*SIZE_CHAIN:(s+1)*SIZE_CHAIN, :, :] = block[i*SIZE_CHAIN:(i+1)*SIZE_CHAIN, :, :]

    ### Attribution de l'évènement

    # Paramètres de la fonction d'attribution
    To = event['intensity'] - bias # idem
    projF = prior['projF'].sel(name='GMST').values
    projC = prior['projC'].sel(name='GMST').values
    idx_event = int(np.argwhere(prior['time'] == event['date'].year).ravel())

    ## Construction de la covariable dans le monde factuel et contre-factuel
    n_sample = N_SAMPLES_COV*SIZE_CHAIN
    n_scenario = prior['n_scenario']
    ntime = prior['time'].size
    x_dims = ["scenario", "sample", "time"]
    x_coords = [range(n_scenario), range(n_sample), range(ntime)]

    # On transforme dans l'espace de la covariable
    XF = xr.DataArray(
        np.stack([hpars[:, i, :] @ projF[i, :, :].T for i in range(n_scenario)]),
        dims=x_dims,
        coords=x_coords
    )

    XC = xr.DataArray(
        np.stack([hpars[:, i, :] @ projC[i, :, :].T for i in range(n_scenario)]),
        dims=x_dims,
        coords=x_coords
    )

    ## Construction des paramètres non-stationnaires
    law = prior['cnslaw']()
    p_dims = ["sample", "scenario", "hpar"]
    p_coords = [range(n_sample), range(n_scenario), list(law.h_name)]
    # Rappel : On conserve les mêmes mêmes tirages MCMC entre scénario. Seule la covariable change
    nspars = xr.DataArray(
        hpars[:, :, -law.nhpar:], # Conserve de hpars uniquement les paramètres de loi
        dims=p_dims,
        coords=p_coords
    )

    # Composition des paramtères finaux e.g mu(t) = mu0 + X(t)*mu1 etc...
    kwargsF = law.draw_params(XF, nspars) # Dictionnaire avec DataArray (sample, scenario, time) pour chaque param
    kwargsC = law.draw_params(XC, nspars)

    # Transposition
    kwargsF = { key : kwargsF[key].transpose("scenario", "time", "sample") for key in kwargsF }
    kwargsC = { key : kwargsC[key].transpose("scenario", "time", "sample") for key in kwargsF }

    ## Calcul des statistiques de l'évènement
    
    # Initialisation des sorties
    pF = np.zeros((n_scenario, ntime, n_sample)) + np.nan
    pF = np.zeros((n_scenario, ntime, n_sample)) + np.nan
    IF = np.zeros((n_scenario, ntime, n_sample)) + np.nan
    IC = np.zeros((n_scenario, ntime, n_sample)) + np.nan

    # Calcul des probabilités factuelles et contre-factuelles
    pF = law.cdf_sf(To, side=prior['side'], **kwargsF)
    pC = law.cdf_sf(To, side=prior['side'], **kwargsC)
    # Bornes à 10x la précision machine
    e = 10 * sys.float_info.epsilon
    pF = np.where(pF > e, pF, e)
    pC = np.where(pC > e, pC, e)
    pF = np.where(pF < 1-e, pF, 1-e)
    pC = np.where(pC < 1-e, pC, 1-e)


    # Calcul des intensités factuelles et contre-factuelles
    pf = np.broadcast_to(pF[:, idx_event, :][:, np.newaxis, :], pF.shape)
    IF = law.icdf_sf(pf, side=prior['side'], **kwargsF) + bias
    IC = law.icdf_sf(pf, side=prior['side'], **kwargsC) + bias

    # Durées de retour, PR et DeltaI
    RF = 1./pF
    RC = 1./pC
    dI = IF - IC
    PR = pF/pC

    ## Calcul de la médiane et de son incertitude
    # On conserve également les paramètres non stationnaires de la loi utilisée
    data = [pF, pC, IF, IC, dI, PR, RF, RC] + [kwargsF[_].values for _ in kwargsF.keys()]
    keys = ["pF","pC","IF","IC","dI","PR", "RF", "RC"] + [f"{param}F" for param in kwargsF.keys()]
    result_dict  = { key : data[ikey] for ikey,key in enumerate(keys) }

    # Conversion en xr.Dataset
    scenarios = ['ssp370', 'ssp585']
    time = prior['time'] # 1850 -- 2100
    modes = np.array(["QL","BE","QU"])

    data_arrays = []
    
    for key, value in result_dict.items():
        array = np.quantile(value, [CI/2, 0.5, 1-CI/2], axis=-1, method='median_unbiased').transpose((1,2,0))
        da = xr.DataArray(
            array,
            coords=[scenarios, time, modes],
            dims=['scenario', 'time', 'quantile'],
            name=key
        )
        data_arrays.append(da)

    dataset = xr.Dataset({da.name: da for da in data_arrays})

    dataset.attrs['time'] = int(event['date'].year)
    dataset['bias'] = bias

    if save_to_disk:
        if event['method'] == 'yearmax':
            if event['extreme_type'] == 'hot':
                var_name = f'tmx{event['duration']}d'
            elif event['extreme_type'] == 'cold':
                var_name = f'tmn{event['duration']}d'
        elif event['method'] == 'calendar':
            if event['extreme_type'] == 'hot':
                window = _best_window_from_range(_datetime_to_doy(event['start_date']),
                                                 _datetime_to_doy(event['stop_date']))
                var_name = f'tmx3d15w_{window[0]:03d}-{window[1]:03d}'

        dataset.to_netcdf(f'{var_name}_{event['lat']}_{event['lon'] % 360}_{event['intensity']:.2f}.nc')

    return dataset.sel(scenario=SCENARIO)