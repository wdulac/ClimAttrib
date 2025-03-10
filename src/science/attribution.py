import numpy as np
import xarray as xr
import pandas as pd
import scipy.stats as sc
import SDFC as sd
import NSSEA as ns

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


# Read latitudes and longitudes from the land-sea Mask
# This in turn is used to itentify the correct multi-model synthesis file to
# load.
# Note : Make sure the land-sea mask is consistent with the Geojson grid
_mask_full  = xr.open_dataset(
    path_to_science_dir + "data/land_sea_mask_IPCC_antarctica.nc"
)
_lat = _mask_full.lat.data
_lon = _mask_full.lon.data

# Global parameters used for the calculations
TIME_REFERENCE = np.arange(1961, 1991, 1, dtype=int)
NS_LAW = ns.models.GEV()
VERBOSE = "--not-verbose"


def _load_obs(lat: float, lon: float) -> tuple:
    """
    Return observed covariate (GSAT timeseries) and the observed variable
    timeseries at the given grid point.

    TODO Add support for more variables than tx3d
    """

    lon = lon % 360 # Convert to 0 -- 360°

    ## Load covariate
    dXo_full = pd.read_csv(
        path_to_data_parent_dir + 'data/Xo/HadCRUT5_GSAT.csv'
    )
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


def compute_event_stats(event: dict) -> tuple:
    """
    Computes the probability in both factual and counter-factual worlds for the
    given event.
    """

    # Load obs and retrieve event intensity To
    # TODO Read intensity from ERA5 using selected date
    Xo, Yo = _load_obs(event['lat'], event['lon'])
    To = Yo.loc[event['date'].year]

    # Convert Yo to anomaly w.r.t :TIME_REFERENCE:
    bias_Yo = Yo.loc[TIME_REFERENCE].mean()
    bias_Xo = Xo.loc[TIME_REFERENCE].mean()
    Yo -= bias_Yo
    Xo -= bias_Xo
    
    ## Load muli-model synthesis
    # Find out indice of lat / lon
    idx_lat = list(_lat).index(event['lat'])
    idx_lon = list(_lon).index(event['lon'] % 360) # Convert to 0 - 360
    # Load file
    climMM_file = path_to_data_parent_dir + \
        'data/climMM/' + \
        f'climMM_lat{idx_lat}_lon{idx_lon}.nc'
    climMM = ns.Climatology.from_netcdf(climMM_file, NS_LAW)

    # Constrain the multi-model synthesis covariate X with observed Xo
    climCX = ns.constrain_covariate(
        climMM,
        Xo,
        TIME_REFERENCE,
        assume_good_scale=True,
        verbose=VERBOSE
    )

    # Constrain with observed variable Yo
    bayes_kwargs = {
        "n_ess": int(10000/(len(climCX.data.sample)-1)) # 10000 tirages
    } 
    climCXCB = ns.stan_constrain(
        climCX,
        Yo,
        path_to_science_dir + 'stan_files/GEV_non_stationary.stan',
        **bayes_kwargs
    )

    ## Output
    ny = climCXCB.n_time
    nsample_MCMC = climCXCB.data.sample_MCMC.shape[0]
    samples_MCMC = climCXCB.data.sample_MCMC
    To_anomaly = To-bias_Yo
    n_stat = 3

    # Initialize output array
    stats = xr.DataArray(
                np.zeros((ny, nsample_MCMC, n_stat)),
                coords=[climCXCB.X.time, samples_MCMC, ["pC","pF", "PR"]],
                dims = ["time","sample_MCMC","stats"]
            )
    # Repeat covariate's best estimate nsample_MCMC times
    XF = xr.DataArray(
                np.tile(
                    climCXCB.X.loc[:,"BE","F","Multi_Synthesis"],
                    (nsample_MCMC, 1)
                ).T,
                coords=[climCXCB.X.time, samples_MCMC],
                dims = ["time","sample_MCMC"]
            )
    XC = xr.DataArray(
                np.tile(
                    climCXCB.X.loc[:,"BE","C","Multi_Synthesis"],
                    (nsample_MCMC, 1)
                ).T,
                coords=[climCXCB.X.time, samples_MCMC],
                dims = ["time","sample_MCMC"]
            )

    ## Build non-stationnary GEV parameters in both factual and counter-factual
    # Factual
    locF  = climCXCB.law_coef.loc["loc0",:,"Multi_Synthesis"] +\
        XF * climCXCB.law_coef.loc["loc1",:,"Multi_Synthesis"]

    scaleF = np.exp(
        climCXCB.law_coef.loc["scale0",:,"Multi_Synthesis"] +\
            XF * climCXCB.law_coef.loc["scale1",:,"Multi_Synthesis"]
    )
    
    # Counter-factual
    locC  = climCXCB.law_coef.loc["loc0",:,"Multi_Synthesis"] +\
        XC * climCXCB.law_coef.loc["loc1",:,"Multi_Synthesis"]
    
    scaleC = np.exp(
        climCXCB.law_coef.loc["scale0",:,"Multi_Synthesis"] +\
            XC * climCXCB.law_coef.loc["scale1",:,"Multi_Synthesis"]
    )

    # Stationary shape param, implies unchanged between F/C since not dependant
    # on the covariate 
    shape = climCXCB.law_coef.loc["shape0",:,"Multi_Synthesis"] +\
        xr.zeros_like(locF)

    ## Compute probability with time
    # Factual
    stats.loc[:,:,"pF"] = sc.genextreme.sf(
        To_anomaly,
        loc=locF,
        scale=scaleF,
        c=-shape
    ).T

    # Counter-factual
    stats.loc[:,:,"pC"] = sc.genextreme.sf(
        To_anomaly,
        loc=locC,
        scale=scaleC,
        c=-shape
    ).T

    ## Compute probability ratio
    stats.loc[:, :, 'PR'] = stats.loc[:,:,"pF"] / stats.loc[:,:,"pC"]

    # Note : returning climMM and climCXCB is only useful to plot GEV params
    return stats