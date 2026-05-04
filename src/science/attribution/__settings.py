"""
Scientific parameters for the attribution algorithm.

All constants here are module-level and imported with ``*`` by ``event_attribution.py``
and ``__data_loading.py``:

- ``N_SAMPLES_COV`` — number of covariate (GMST) samples drawn from the prior (100).
- ``SIZE_CHAIN`` — number of posterior samples per MCMC chain (100).
- ``METHOD_CONSTRAINT`` — dict specifying how the GMST covariate is used in the
  constraint (``{'GMST': 'full'}``).
- ``USE_STAN`` — whether to use the Stan MCMC backend (True) or a pure-Python
  fallback.
- ``MASTER_SEED`` — global random seed for reproducibility (from env var
  ``MASTER_SEED``, default 123456).
- ``STAN_WORK_DIR`` — directory where compiled Stan model binaries are cached.
- ``N_SAMPLES_ATTRIB`` — number of hyperparameter samples used for confidence
  interval estimation (1000).
- ``CI`` — half-width of the confidence interval (0.1 → 5th–95th percentile range).
- ``SCENARIO`` — climate scenario used for results returned to the user (``'ssp370'``).
"""

import os
from app_platform.shared.paths import DATA, SRC


## Paramètres généraux
# Pour la contrainte Y
N_SAMPLES_COV = 100 # Tirages de covariables
SIZE_CHAIN = 100 # Nombre de valeur extraites de chaque chaine (Une chaine par tirage de covariable)
METHOD_CONSTRAINT = {'GMST': 'full'}
USE_STAN = True
MASTER_SEED = int(os.getenv('MASTER_SEED', 123456))
STAN_WORK_DIR =  SRC / 'science/stan_files/'

# Pour l'attribution
N_SAMPLES_ATTRIB = 1000 # Nombre de valeurs de hpars à tirer pour l'intervalle de confiance
MODE = 'quantile'
CI = 0.1
SCENARIO = 'ssp370'
