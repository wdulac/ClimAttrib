import xarray as xr
import datetime as dt

import ANKIALE as ank
from ANKIALE.stats import MPeriodSmoother

from .__calendar_utils import _datetime_to_doy, _best_window_from_range
from .__settings import *


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
            file_suffix = var_name
        elif extreme_type == 'cold':
            var_name = f'tmn{duration}d'
            file_suffix = var_name
    elif computation_method == 'calendar':
        if extreme_type == 'hot':
            var_name = 'tmx3d15w'
            window = _best_window_from_range(_datetime_to_doy(start_date),
                                             _datetime_to_doy(stop_date))
            file_suffix = f"{var_name}_{window[0]:03d}-{window[1]:03d}"
        elif extreme_type == 'cold':
            raise NotImplementedError


    Yo_file = DATA / f'Yo/{var_name}/Yo_{file_suffix}.nc'

    Yo = xr.open_dataset(Yo_file)[var_name].sel(lat=lat, lon=lon)

    # On remplace l'axe du temps par les années
    Yo = xr.DataArray(Yo.values, dims=Yo.dims,
                      coords = [Yo.time.dt.year.values] + [Yo.coords[d] for d in Yo.dims[1:]])
    
    return Yo