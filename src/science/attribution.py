import numpy as np
import xarray as xr
import pandas as pd

import datetime as dt

import ANKIALE as ank
# Specific imports
from ANKIALE.cmd.__cmd_constrain import zgaussian_conditionning
from ANKIALE.cmd.__cmd_constrain import zmcmc
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
METHOD = 'INDEPENDANT'

# Pour la contrainte Y
N_SAMPLES_COV = 100 # Tirages de covariables
SIZE_CHAIN = 100 # Nombre de valeur extraites de chaque chaine (Une chaine par tirage de covariable)
USE_STAN = True

# Pour l'attribution
N_SAMPLES_ATTRIB = 1000 # Nombre de valeurs de hpars à tirer pour l'intervalle de confiance
SIDE = 'right'
MODE = 'quantile'
CI = 0.05


def _projection_operator(clim, times):
    ## Build projection operator for the covariable
    time = clim.time
    spl,lin,_,_ = clim.build_design_XFC()
    nper = len(clim.dpers)

    design_ = []
    for nameX in clim.namesX:
        if nameX == clim.cname:
            design_ = design_ + [spl for _ in range(nper)] + [nper * lin]
        else:
            design_ = design_ + [np.zeros_like(spl) for _ in range(nper)] + [np.zeros_like(lin)]
    design_ = design_ + [np.zeros( (time.size,clim.sizeY) )]
    design_ = np.hstack(design_)

    T = xr.DataArray( np.identity(design_.shape[0]) , dims = ["timeA","timeB"] , coords = [time,time] ).loc[times,time].values
    A = T @ design_ / nper

    return A


def _load_obs(lat: float, lon: float) -> tuple[xr.DataArray, xr.DataArray]:

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

    clim_file = path_to_data_parent_dir + 'data/SYNTHESIS.nc'
    clim = ank.Climatology.init_from_file(clim_file)

    # hpar et hcov du prior
    hpar_prior = clim.hpar.sel(lat=event['lat'], lon=event['lon'] % 360,
                               drop=False)
    hcov_prior = clim.hcov.sel(lat=event['lat'], lon=event['lon'] % 360,
                               drop=False)

    # La loi statistique utilisée (ici GEV)
    nslaw = clim._nslaw_class

    # L'axe du temps de référence
    time = clim.time

    # Période de référence pour le calcul du biais
    bper = clim.bper

    # Matrices de projection factuel / contre-factuel
    projF, projC = clim.projection()

    # Lecture des observations
    Xo, Yo = _load_obs(event['lat'], event['lon'])

    # Calcul du biais. On pourrait utiliser la valeur stockée dans :clim: mais elle est légèrement différente.
    bias_arr = Yo.sel( time = slice(*[str(y) for y in bper]) ).mean('time')

    # Expression de la variable en anomalie
    Yo_anom = Yo - bias_arr

    ### Contrainte par la covariable

    # Paramètres de la fonction de conditionnement
    ihpar = hpar_prior.transpose('lat', 'lon', 'hpar').values
    ihcov = hcov_prior.transpose('lat', 'lon', 'hpar0', 'hpar1').values
    iXo = Xo.values[np.newaxis, np.newaxis, :] # On ajoute deux dimensions pour représenter (lat, lon) en mono point de grille
    timeXo = Xo.time
    A_Xo = _projection_operator(clim, timeXo)

    # Application de la contrainte par la covariable
    hpar_CX, hcov_CX = zgaussian_conditionning(ihpar, ihcov, iXo, A=A_Xo, timeXo=timeXo, method=METHOD)

    ### Contrainte par les observations de la variable

    # Initialisation de Stan dans un répertoire fixe
    stan_work_dir = path_to_science_dir + './stan_files/'
    nslaw().init_stan(tmp=stan_work_dir, force_compile=False) # On compile uniquement si les fichiers sont absents

    # Paramètres de la fonction mcmc
    ihpar = hpar_CX[:,:, np.newaxis, :] # (lat, lon, sample, hpar)
    ihcov = hcov_CX[:,:, np.newaxis, :, :] # (lat, lon, sample, hpar0, hpar1)
    iYo_anom = Yo_anom.values[np.newaxis, np.newaxis, np.newaxis, :] # (lat, lon, sample, time)
    samples = np.arange(N_SAMPLES_COV)
    A_Yo = _projection_operator(clim, Yo.time)

    # On applique la contrainte Y
    ohpars = zmcmc(ihpar, ihcov, iYo_anom, samples, A_Yo, SIZE_CHAIN, nslaw, USE_STAN, stan_work_dir)
    # On transpose pour avoir (lat, lon, hpar, sample, chain)
    ohpars = ohpars.transpose(0, 1, 3, 2, 4)
    hpar_CXCB, hcov_CXCB = mean_cov_hpars(ohpars) # Calcul des paramètres de la distribution des tirages MCMC

    ### Attribution de l'évènement

    # Paramètre de la fonction d'attribution
    ihpar = hpar_CXCB[:, :, np.newaxis, :] # (lat, lon, period, hpar).
    ihcov = hcov_CXCB[:, :, np.newaxis, :, :] # (lat, lon, period, hpar0, hpar1)
    bias = bias_arr.values[np.newaxis, np.newaxis, np.newaxis] # (lat, lon, period)
    To = event['intensity'] - bias # idem
    iprojF = projF.values
    iprojC = projC.values
    idx_event = int(np.argwhere(time == event['date'].year).ravel())

    # Calcul des statistiques de l'évènement
    out_CXCB = zattribute_event(ihpar, ihcov, bias, To, iprojF, iprojC, idx_event, nslaw, SIDE, MODE, N_SAMPLES_ATTRIB, CI)
    keys = ["pF","pC","RF","RC","IF","IC","dI","PR"]
    out_CXCB  = { key : out_CXCB[ikey][0,0,0,:,:] for ikey,key in enumerate(keys) } # Mono point de grille + mono scénario'

    # Conversion en xr.Dataset
    modes =np.array(["QL","BE","QU"])

    data_arrays = []

    for key, value in out_CXCB.items():
        da = xr.DataArray(
            value,
            coords=[time, modes],
            dims=['time', 'quantile'],
            name=key
        )
        data_arrays.append(da)

    dataset = xr.Dataset({da.name: da for da in data_arrays})

    return dataset