import numpy as np
import xarray as xr
import pandas as pd
import scipy.stats as sc
import SDFC as sd
import NSSEA as ns

# Evaluate relative path to the directory right above `data` This mostly serves
# as a compatibility patch for VsCode interactive mode as the cwd in production
# mode should always be `app/`
import os

current_dir = os.path.basename(os.getcwd())
if current_dir == 'science':
    path_to_data_parent_dir = '../../'
elif current_dir == 'app':
    path_to_data_parent_dir = './'


# Read latitudes and longitudes from the land-sea Mask
# This in turn is used to itentify the correct multi-model synthesis file to
# load.
# Note : Make sure the land-sea mask is consistent with the Geojson grid
mask_full  = xr.open_dataset(
    path_to_data_parent_dir + "data/land_sea_mask_IPCC_antarctica.nc"
)
mask = mask_full.land_sea_mask
lat = mask.lat
lon = mask.lon

# Global parameters used for the calculations
time_reference = np.arange(1961, 1991, 1, dtype=int )
bayes_kwargs = { "n_mcmc_drawn_min" : 2500 , "n_mcmc_drawn_max" : 5000 }
n_sample = 1000
ns_law = ns.models.GEV()
verbose = "--not-verbose"
ci = 0.05


def load_obs(lat: float, lon: float) -> tuple:
    """
    Return observed covariate (GSAT timeseries) and the observed variable
    timeseries at the given grid point.

    TODO Add support for more variables than tx3d
    """

    lon = lon % 360 # Convert to 0 -- 360°

    ## Load covariate
    dXo_full = pd.read_csv(path_to_data_parent_dir + 'data/Xo/HadCRUT5_GSAT.csv')
    year_Xo = dXo_full.loc[:,"Time"].array
    dXo_sub = dXo_full.drop(
        ["Fraction of area represented", "Coverage uncertainty (1 sigma)"],
        axis=1
    )
    # Median over 200 realizations
    dXo = dXo_sub.median(axis=1)
    dXo.index = year_Xo
    Xo = pd.DataFrame(dXo)

    # Load variable at chosen grid point
    dYo_full   = xr.open_dataset(
        path_to_data_parent_dir + "data/Yo/tx3d/tx3d_era5_1940-2022_g025.nc" 
    )
    dYo = dYo_full.sel(lat=lat, lon=lon) # Do not use method='nearest' for now
    Yo = pd.DataFrame(dYo.tasmax, index=dYo.time.dt.year)

    return Xo, Yo


def attribute_event(event: dict) -> tuple:
    """
    TODO Docstring
    """

    # Load obs and retrieve event intensity To
    Xo, Yo = load_obs(event['lat'], event['lon'])
    To = Yo.loc[event['Date'].year]

    # Convert Yo to anomaly w.r.t :time_reference:
    bias_Yo = Yo.loc[time_reference].mean()
    bias_Xo = Xo.loc[time_reference].mean()
    Yo -= bias_Yo
    Xo -= bias_Xo
    
    ## Load muli-model synthesis
    # Find out indice of lat / lon
    idx_lat = list(lat.data).index(event['lat'])
    idx_lon = list(lon.data).index(event['lon'] % 360) # Convert to 0 - 360
    # Load file
    climMM_file = path_to_data_parent_dir + \
        'data/climMM/' + \
        f'climMM_lat{idx_lat}_lon{idx_lon}.nc'
    # climMM = ns.Climatology.from_netcdf(climMM_file, ns_law)


