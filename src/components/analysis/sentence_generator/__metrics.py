from .__data_models import CIValue, Metrics


def q(ds, var, t, qlabel='BE'):
    return float(ds[var].sel(time=t, quantile=qlabel))


def extract_ci(ds, var, t):
    return CIValue(
        value=q(ds, var, t, 'BE'),
        ql=q(ds, var, t, 'QL'),
        qu=q(ds, var, t, 'QU'),
    )


def safe_inv(x: float) -> float:
    return float('nan') if x is None or x == 0 else 1.0 / x


def invert_ci(ci: CIValue):
    return CIValue(
        value=safe_inv(ci.value),
        ql=safe_inv(ci.qu),
        qu=safe_inv(ci.ql),
    )


def build_metrics(stats, t):

    def to_celsius(ci):
        return CIValue(
            value=ci.value - 273.15,
            ql=ci.ql - 273.15,
            qu=ci.qu - 273.15,
        )

    pF = extract_ci(stats, "pF", t)
    pC = extract_ci(stats, "pC", t)
    PR = extract_ci(stats, "PR", t)
    RP_F = extract_ci(stats, "RF", t)
    RP_C = extract_ci(stats, "RC", t)
    IF = to_celsius(extract_ci(stats, "IF", t))
    IC = to_celsius(extract_ci(stats, "IC", t))
    dI = extract_ci(stats, "dI", t)
    FAR = extract_ci(stats, "FAR", t)

    return Metrics(
        pF=pF,
        pC=pC,
        PR=PR,
        PR_inv=invert_ci(PR),
        FAR=FAR,
        RP_F=RP_F,
        RP_C=RP_C,
        IF=IF,
        IC=IC,
        dI=dI
    )