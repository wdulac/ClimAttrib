import numpy as np
import xarray as xr
import pandas as pd

import datetime as dt

import ANKIALE as ank
# Specific imports
from ANKIALE.stats.__constraint import gaussian_conditionning
from ANKIALE.stats.__constraint import mcmc
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

# Pour la contrainte X
METHOD = 'MAR2'

# Pour la contrainte Y
N_SAMPLES_COV = 100 # Tirages de covariables
SIZE_CHAIN = 100 # Nombre de valeur extraites de chaque chaine (Une chaine par tirage de covariable)
USE_STAN = True

# Pour l'attribution
N_SAMPLES_ATTRIB = 1000 # Nombre de valeurs de hpars à tirer pour l'intervalle de confiance
SIDE = 'right'
MODE = 'quantile'
CI = 0.05

# Loading the prior
_CLIM_FILE = path_to_data_parent_dir + 'data/SYNTHESIS_EBM.nc'
CLIM = ank.Climatology.init_from_file(_CLIM_FILE)
# Set XN to CMIP5 (custom file dropped in place of CMIP5 forcings: it's actually dT from EBM made from CMIP6 forcings file)
CLIM._Xconfig['XN_version'] = 'CMIP5'
# Initializing CmdStan local work directory
STAN_WORK_DIR = path_to_science_dir + './stan_files/'
NSLAW = CLIM._nslaw_class
NSLAW().init_stan(tmp=STAN_WORK_DIR, force_compile=False)
# Total time axis (1850 -- 2100)
TIME = CLIM.time
# Reference period for bias
BPER = CLIM.bper
# Matrices de projection factuel / contre-factuel
PROJF, PROJC = CLIM.projection()


def _projection_operator(times):

    time = CLIM.time
    lin, spl = CLIM.build_design_basis()
    nper = len(CLIM.dpers)

    design_ = []
    for nameX in CLIM.namesX:
        if nameX == CLIM.cname:
            design_ = design_ + [spl[nameX][CLIM.dpers[iper]] for iper in range(nper)] + [nper * lin]
        else:
            design_ = design_ + [np.zeros_like(spl[nameX][CLIM.dpers[iper]]) for iper in range(nper)] + [np.zeros_like(lin)]
    design_ = design_ + [np.zeros( (time.size,CLIM.sizeY) )]
    design_ = np.hstack(design_)

    T = xr.DataArray( np.identity(design_.shape[0]) , dims = ["timeA","timeB"] , coords = [time,time] ).loc[times,time].values
    A = T @ design_ / nper

    return A


def _load_obs(lat: float, lon: float) -> tuple[xr.DataArray, xr.DataArray]:
    """
    Return observed covariate (GSAT timeseries) and the observed variable
    timeseries at the given grid point.

    TODO Add support for more variables than tx3d
    """

    # Convert to 0 -- 360°
    lon = lon % 360

    Xo_file = path_to_data_parent_dir + 'data/Xo/HadCRUT5_GSAT.nc'
    Yo_file = path_to_data_parent_dir + 'data/Yo/tx3d/tx3d_era5_1940-2022_g025.nc'

    Xo = xr.open_dataset(Xo_file)['tas']
    Yo = xr.open_dataset(Yo_file)['tasmax'].sel(lat=lat, lon=lon)

    # On remplace l'axe du temps par les années
    Xo = xr.DataArray(Xo.values, dims=Xo.dims,
                      coords=[Xo.time.dt.year.values] + [Xo.coords[d] for d in Xo.dims[1:]])
    Yo = xr.DataArray(Yo.values, dims=Yo.dims,
                      coords = [Yo.time.dt.year.values] + [Yo.coords[d] for d in Yo.dims[1:]])
    
    return Xo, Yo


def attribute_event(event:dict) -> xr.Dataset:

    # hpar et hcov du prior
    hpar_prior = CLIM.hpar.sel(lat=event['lat'], lon=event['lon'] % 360)
    hcov_prior = CLIM.hcov.sel(lat=event['lat'], lon=event['lon'] % 360)

    # Lecture des observations
    Xo, Yo = _load_obs(event['lat'], event['lon'])

    # Calcul du biais. On pourrait utiliser la valeur stockée dans :CLIM: mais elle est légèrement différente.
    bias_arr = Yo.sel( time = slice(*[str(y) for y in BPER]) ).mean('time')

    # Expression de la variable en anomalie
    Yo_anom = Yo - bias_arr

    ### Contrainte par la covariable

    # Paramètres de la fonction de conditionnement
    ihpar = hpar_prior.values
    ihcov = hcov_prior.values
    iXo = Xo.values
    timeXo = Xo.time
    A_Xo = _projection_operator(timeXo)

    # Application de la contrainte par la covariable
    hpar_CX, hcov_CX = gaussian_conditionning(ihpar, ihcov, iXo, A=A_Xo, timeXo=timeXo, method=METHOD)

    ### Contrainte par les observations de la variable

    # Paramètres de la fonction mcmc
    iYo_anom = Yo_anom.values
    samples = np.arange(N_SAMPLES_COV)
    A_Yo = _projection_operator(Yo.time)

    # Initialisation du résultat
    ohpars = np.zeros((ihpar.size, samples.size, SIZE_CHAIN)) + np.nan
    # Boucle sur les tirages de covariable
    mcmc_args = [SIZE_CHAIN, NSLAW, USE_STAN, STAN_WORK_DIR]
    for s in samples:
        oh = mcmc(hpar_CX, hcov_CX, iYo_anom, A_Yo, *mcmc_args)
        ohpars[:,s,:] = oh
    
    # calcul des paramètres de la distribution des tirages MCMC
    hpar_CXCB, hcov_CXCB = mean_cov_hpars(ohpars)

    ### Attribution de l'évènement

    # Paramètre de la fonction d'attribution
    ihpar = hpar_CXCB[np.newaxis, np.newaxis, np.newaxis, :] # (lat, lon, period, hpar).
    ihcov = hcov_CXCB[np.newaxis, np.newaxis, np.newaxis, :, :] # (lat, lon, period, hpar0, hpar1)
    bias = bias_arr.values[np.newaxis, np.newaxis, np.newaxis] # (lat, lon, period)
    To = event['intensity'] - bias # idem
    iprojF = PROJF.values
    iprojC = PROJC.values
    idx_event = int(np.argwhere(TIME == event['date'].year).ravel())

    # Calcul des statistiques de l'évènement
    out_CXCB = zattribute_event(ihpar, ihcov, bias, To, iprojF, iprojC, idx_event, NSLAW, SIDE, MODE, N_SAMPLES_ATTRIB, CI)
    keys = ["pF","pC","RF","RC","IF","IC","dI","PR"]
    out_CXCB  = { key : out_CXCB[ikey][0,0,0,:,:] for ikey,key in enumerate(keys) } # Mono point de grille + mono scénario'

    # Conversion en xr.Dataset
    modes = np.array(["QL","BE","QU"])
    data_arrays = []
    
    for key, value in out_CXCB.items():
        da = xr.DataArray(
            value,
            coords=[TIME, modes],
            dims=['time', 'quantile'],
            name=key
        )
        data_arrays.append(da)

    dataset = xr.Dataset({da.name: da for da in data_arrays})

    dataset.attrs['time'] = int(event['date'].year)

    return dataset