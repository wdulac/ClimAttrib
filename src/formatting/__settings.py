DEFAULT_SIG = 2
PROB_SOFT_MIN = 0.01 # Expressed as percentage
PROB_SOFT_MAX = 99.9 # Expressed as percentage

RET_SOFT_MAX = 1 / (1e-3 * PROB_SOFT_MIN) # e.g 0.01 % -> 10 000 year return period