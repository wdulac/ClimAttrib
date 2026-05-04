"""
Data classes for the sentence generator.

- ``CIValue(value, ql, qu)`` — a scalar metric together with its lower and upper
  confidence interval bounds (QL = 5th percentile, QU = 95th percentile).
- ``Metrics`` — a named collection of ``CIValue`` instances covering all attribution
  outputs for a single point in time: ``pF``, ``pC``, ``PR``, ``PR_inv``, ``FAR``,
  ``RP_F``, ``RP_C``, ``IF``, ``IC``, ``dI``.
"""

from dataclasses import dataclass

@dataclass
class CIValue:
    value: float
    ql: float
    qu: float

@dataclass
class Metrics:
    pF: CIValue
    pC: CIValue
    PR: CIValue
    PR_inv: CIValue
    FAR: CIValue
    RP_F: CIValue
    RP_C: CIValue
    IF: CIValue
    IC: CIValue
    dI: CIValue
