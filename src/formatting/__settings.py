DEFAULT_SIG = 2
PROB_SOFT_MIN = 0.01 # Expressed as percentage
PROB_SOFT_MAX = 99.9 # Expressed as percentage

RET_SOFT_MAX = 1 / (1e-2 * PROB_SOFT_MIN) # e.g 0.01 % -> 10 000 year return period

DEFAULT_THOUSAND_SEP = ","

PR_SOFT_MIN = 0.00001
PR_SOFT_MAX = 100000

FAR_SIG_THRESHOLD = 99 # FAR threshold (%) above which the amount of significant digits is increased
FAR_SIG_SECONDARY = DEFAULT_SIG + 2
FAR_SOFT_MAX = 99.99 # Expressed as percentage
FAR_NAN_STR = '--'