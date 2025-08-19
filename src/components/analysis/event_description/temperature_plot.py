import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
import xarray as xr

from pathlib import Path

from io import BytesIO
import base64



def _fig_to_uri(in_fig: matplotlib.figure.Figure, close_all=True, **save_args) -> str:
    """
    Save a figure as a URI
    :param in_fig:
    :return:
    """
    out_img = BytesIO()
    in_fig.savefig(out_img, format='png', **save_args)
    if close_all:
        in_fig.clf()
        plt.close('all')
    out_img.seek(0)  # rewind file
    encoded = base64.b64encode(out_img.read()).decode("ascii").replace("\n", "")
    return "data:image/png;base64,{}".format(encoded)


def _identify_Yo_filename(event: dict | None = None) -> str:

    return Path('data/Yo/tx3d/tx3d_era5_1940-2022_g025.nc')


def _load_observed_timeseries(event) -> xr.DataArray:

    filename = _identify_Yo_filename(event)
    lat = event['lat']
    lon = event['lon']
    Yo = xr.open_dataset(filename)['tasmax'].sel(lat=lat, lon=lon)
    Yo = xr.DataArray(Yo.values - 273.15, dims=Yo.dims, coords=[Yo.time.dt.year.values] + [Yo.coords[d] for d in Yo.dims[1:]])
    return Yo


def make_temperature_plot(event: dict) -> str:

    Yo = _load_observed_timeseries(event)

    fig, ax = plt.subplots(figsize=(6,1.5))
    ax.plot(Yo.time, Yo.values, lw=1.2, c='#b5504a')
    ax.set_xlim((Yo.time[0], Yo.time[-1]))
    ax.set_ylim(bottom=np.floor(Yo.min()) - 1)
    ax.grid()

    return _fig_to_uri(fig, bbox_inches='tight')