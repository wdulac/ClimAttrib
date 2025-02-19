import numpy as np
import xarray as xr
import pandas as pd
import scipy.stats as sc
import SDFC as sd
import NSSEA as ns

def load_obs(lat, lon):

    lon = lon % 360 # Convert to 0 -- 360°

    ## Load Xo
    dXo_full = pd.read_csv('../../data/Xo/HadCRUT5_GSAT.csv')
    year_Xo = dXo_full.loc[:,"Time"].values
    dXo_sub = dXo_full.drop(["Fraction of area represented", "Coverage uncertainty (1 sigma)"],axis=1)
    # Médiane de 200 réalisations
    dXo = dXo_sub.median(axis=1)
    dXo.index = year_Xo
    Xo = pd.DataFrame(dXo)
    # Xo  = pd.DataFrame(dXo.values.squeeze(),index = year_Xo )

    dYo_full   = xr.open_dataset("../../data/Yo/tx3d/tx3d_era5_1940-2022_g025.nc" )
    dYo = dYo_full.sel(lat=lat, lon=lon) # Do not use method='nearest' for now
    year_Yo = dYo.time["time.year"].values
    Yo    = pd.DataFrame( dYo.tasmax.values.ravel() , index = year_Yo )
        
    return Xo,Yo