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
