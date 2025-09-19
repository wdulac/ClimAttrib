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

def _projection_matrix(X: dict, vsize: int, smoother, constraint: dict | None = None) -> np.ndarray:

    time_size = X[next(iter(X))].time0.values.size
    return np.hstack((
        build_projection_matrix(smoother, X, constraint),
        np.zeros((time_size, vsize))
    ))


def _load_prior(extreme_type: str) -> dict:

    if extreme_type == 'hot':
        var = 'tmx3d'
        side = 'right'
    elif extreme_type == 'cold':
        var = 'tmn3d'
        side = 'left'

    clim_file = path_to_data_parent_dir + f'data/{var}_CONSTRAIN_X.nc'

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
    

def _load_obs(lat: float, lon: float, extreme_type: str) -> xr.DataArray:
    """
    Return observed covariate (GSAT timeseries) and the observed variable
    timeseries at the given grid point.
    """

    # Convert to 0 -- 360°
    lon = lon % 360

    if extreme_type == 'hot':
        var_dir = 'tm3d'
        var_name = 'tmx3d'
    elif extreme_type == 'cold':
        var_dir = 'tn3d'
        var_name = 'tmn3d'

    Yo_file = path_to_data_parent_dir + f'data/Yo/{var_dir}/{var_name}_ERA5_1940-2022_1p5deg.nc'

    Yo = xr.open_dataset(Yo_file)[var_name].sel(lat=lat, lon=lon)

    # On remplace l'axe du temps par les années
    Yo = xr.DataArray(Yo.values, dims=Yo.dims,
                      coords = [Yo.time.dt.year.values] + [Yo.coords[d] for d in Yo.dims[1:]])
    
    return Yo


def attribute_event(event:dict) -> xr.Dataset:

    prior = _load_prior(event['extreme_type'])

    # Lecture du prior contraint par la covariable
    hpar_CX = prior['hpar'].sel(lat=event['lat'], lon=event['lon'] % 360, drop=True)
    hcov_CX = prior['hcov'].sel(lat=event['lat'], lon=event['lon'] % 360, drop=True)

    # Lecture des observations
    Yo = _load_obs(event['lat'], event['lon'], event['extreme_type'])

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