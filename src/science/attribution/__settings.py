import os
from platform.shared.paths import DATA, SRC


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
CI = 0.05
SCENARIO = 'ssp370'
