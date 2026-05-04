"""
Default thresholds and parameters for the ``formatting`` module.

- ``DEFAULT_SIG`` — default number of significant figures (2).
- ``PROB_SOFT_MIN`` / ``PROB_SOFT_MAX`` — percentage bounds below/above which
  probability strings switch to "< X" / "> X" notation (0.01% and 99.9%).
- ``RET_SOFT_MAX`` — return period above which the string reads "> 10 000 years".
- ``DEFAULT_THOUSAND_SEP`` — thousand separator character for large numbers (",").
- ``PR_SOFT_MIN`` / ``PR_SOFT_MAX`` — ratio bounds for probability ratio formatting.
- ``FAR_SIG_THRESHOLD`` — FAR percentage above which an extra significant figure is
  used (99%).
- ``FAR_SIG_SECONDARY`` — number of sig figs used above the threshold (3).
- ``FAR_SOFT_MAX`` — FAR percentage above which the string reads "> 99.9%" (99.9%).
- ``FAR_NAN_STR`` — string used for NaN FAR values ("--").
"""

DEFAULT_SIG = 2
PROB_SOFT_MIN = 0.01 # Expressed as percentage
PROB_SOFT_MAX = 99.9 # Expressed as percentage

RET_SOFT_MAX = 1 / (1e-2 * PROB_SOFT_MIN) # e.g 0.01 % -> 10 000 year return period

DEFAULT_THOUSAND_SEP = ","

PR_SOFT_MIN = 0.001
PR_SOFT_MAX = 1000

FAR_SIG_THRESHOLD = 99 # FAR threshold (%) above which the amount of significant digits is increased
FAR_SIG_SECONDARY = DEFAULT_SIG + 1
FAR_SOFT_MAX = 99.9 # Expressed as percentage
FAR_NAN_STR = '--'