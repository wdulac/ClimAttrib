"""
Core attribution algorithm.

``attribute_event(event, n_process, save_to_disk)`` runs the full attribution
pipeline for a single event and returns an ``xarray.Dataset`` of attribution
statistics. This function is called by the Celery ``attribution`` task in
``app_platform.compute.celery``.

## Pipeline

1. **Load prior** (``__data_loading._load_prior``) — reads the pre-computed
   constrained climatology for the selected variable (hot/cold, yearmax/calendar,
   duration) from a NetCDF file in ``data/prior/``. The prior encodes the statistical
   distribution of temperature extremes as a function of a covariate (GMST), with
   hyperparameters (``hpar``) and their covariance matrix (``hcov``) at each grid
   point.

2. **Load observations** (``__data_loading._load_obs``) — reads the annual extreme
   timeseries (Yo) for the selected grid point from ``data/Yo/``. If the event
   intensity sets a new record compared to the timeseries, the current year is
   appended before computing the bias.

3. **MCMC constraint** — using ANKIALE's ``constraint_var`` and Stan, samples the
   posterior distribution of the hyperparameters given the observations. The work is
   split across ``n_process`` subprocesses via ``ProcessPoolExecutor``; each process
   handles a subset of the covariate samples (``N_SAMPLES_COV``). ``OMP_NUM_THREADS``
   and ``MKL_NUM_THREADS`` are kept at 1 inside worker processes to avoid
   thread-level oversubscription.

4. **Compute attribution metrics** — from the constrained hyperparameters, derives:
   factual (pF) and counterfactual (pC) probabilities, their ratio (PR), fraction of
   attributable risk (FAR), return periods (RF, RC), and intensity estimates (IF, IC,
   dI) for two climate scenarios (ssp370, ssp585) across the full 1850–2100 time axis.
   Confidence intervals are computed as the 5th–95th percentile range across MCMC
   samples.

5. **Return** — an ``xr.Dataset`` with dimensions ``(scenario, time, quantile)``
   keyed by variable name (pF, pC, PR, FAR, RF, RC, IF, IC, dI, plus the law
   parameters). Only the scenario defined in ``__settings.SCENARIO`` is returned to
   the caller.
"""

import sys
import numpy as np
import xarray as xr
import datetime as dt

from ANKIALE.stats.__constraint import constraint_var

from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Sequence, Tuple

from .__data_loading import _load_prior, _load_obs
from .__calendar_utils import _best_window_from_range, _datetime_to_doy
from .__settings import *


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

    ## Calcul des quantiles
    # On conserve également les paramètres non stationnaires de la loi utilisée
    data = [pF, pC, IF, IC, dI, RF, RC] + [kwargsF[_].values for _ in kwargsF.keys()]
    keys = ["pF","pC","IF","IC","dI","RF","RC"] + [f"{param}F" for param in kwargsF.keys()]
    # result_dict  = { key : data[ikey] for ikey,key in enumerate(keys) }

    result_dict = {}
    for key, value in zip(keys, data):
        q = np.quantile(value, [CI/2, 0.5, 1-CI/2], axis=-1, method='median_unbiased')
        q = q.transpose((1,2,0)) # (scenario, time, quantile)

        # Remplacement des bornes par 0 ou inf quand applicable sur la proba et la durée de retour
        if key in ['pF', 'pC']:
            q = np.where(q == e, 0.0, q)
            q = np.where(q == 1-e, 1.0, q)
        elif key in ["RF", "RC"]:
            q = np.where(q == 1/e, np.inf, q)

        result_dict[key] = q

    ## Construction PR depuis pF / pC

    PR_samples = pF / pC # PR à partir des samples clippés entre e et 1-e

    # On réintroduit les bornes e et 1/e et inf en fonction de pF et pC
    PR_samples = np.where(pC == e, 1/e, PR_samples)
    PR_samples = np.where(pF == e, e, PR_samples)
    PR_samples = np.where((pC == e) & (pF == e), 1, PR_samples)

    # Calcul des quantiles sur le PR clippé et correctement borné entre e et 1/e
    PR_q = np.quantile(PR_samples, [CI/2, 0.5, 1-CI/2], axis=-1, method="median_unbiased").transpose((1,2,0))

    # On remplace les bornes e et 1/e par respectivement 0 et infini
    PR_q = np.where(PR_q == 1/e, np.inf, PR_q)
    PR_q = np.where(PR_q == e, 0.0, PR_q)

    result_dict["PR"] = PR_q

    ## Construction du FAR depuis PR

    with np.errstate(divide='ignore', invalid='ignore'):
        FAR_q = 1 - 1 / PR_q

    FAR_q = np.where(PR_q < 1.0, np.nan, FAR_q)

    result_dict["FAR"] = FAR_q

    ## Conversion en xr.Dataset
    scenarios = ['ssp370', 'ssp585']
    time = prior['time'] # 1850 -- 2100
    modes = np.array(["QL","BE","QU"])

    data_arrays = []
    
    for key, array in result_dict.items():
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