import dask
import numpy as np
import pandas as pd
import xarray as xr

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.font_manager as font_manager

import holoviews as hv
from holoviews import dim, opts
from pathlib import Path

from pathlib import Path, PurePath

from snobedo.lib.dask_utils import start_cluster
from snobedo.snotel import SnotelLocations

SHARED_STORE = '/uufs/chpc.utah.edu/common/home/skiles-group1'

SNOBAL_DIR = Path(f'{SHARED_STORE}/erw_isnobal')
SNOTEL_DIR = Path.home() / 'shared-cryosphere/Snotel'
CBRFC_DIR = Path.home() / 'shared-cryosphere/CBRFC'
HRRR_DIR = Path(f'{SHARED_STORE}/HRRR_water_years')
FIGURES_DIR = Path.home() / 'shared-cryosphere/figures'

# Xarray options
# Used in comparison to SNOTEL site locations
COARSEN_OPTS = dict(x=2, y=2)
RESAMPLE_1_DAY_OPTS = dict(time='1D', base=23)


# HRRR helpers
def hrrr_pixel_index(hrrr_file, site):
    x_index = np.abs(hrrr_file.longitude.values - hrrr_longitude(site.lon))
    y_index = np.abs(hrrr_file.latitude.values - site.lat)
    return np.unravel_index((x_index + y_index).argmin(), x_index.shape)


def hrrr_longitude(longitude):
    return longitude % 360


@dask.delayed
def hrrr_snotel_pixel(file, x_pixel_index, y_pixel_index):
    """
    Read GRIB file surface values, remove unsed dimensions, and
    set the time dimension.

    Required to be able to concatenate all GRIB file to a time series
    """
    hrrr_file = xr.open_dataset(
        file.as_posix(),
        engine='cfgrib',
        backend_kwargs={
            'errors': 'ignore',
            'indexpath': '',
            'filter_by_keys': {
                'level': 0,
                'typeOfLevel': 'surface',
            }
        },
    ).isel(x=[x_pixel_index], y=[y_pixel_index])
    del hrrr_file.coords['valid_time']
    del hrrr_file.coords['surface']
    del hrrr_file.coords['step']

    return hrrr_file.expand_dims(time=[hrrr_file.time.values])


# Plot settings and helpers
plt.rcParams.update(
    {
        'axes.labelsize': 10
    }
)

LEGEND_TEXT = "{0:10} {1:8}"
LEGEND_DATE = "%Y-%m-%d"


def legend_text(label, value, color='none'):
    return mpatches.Patch(
        color=color, label=LEGEND_TEXT.format(label, value)
    )


def add_legend_box(ax, entries):
    ax.legend(
        handles=entries,
        loc='upper left',
        prop=font_manager.FontProperties(
            family='monospace', style='normal', size=8
        ),
    )

## Use hvplot
def use_hvplot():
    import hvplot.xarray
    import hvplot.pandas
    pd.options.plotting.backend = 'holoviews'
