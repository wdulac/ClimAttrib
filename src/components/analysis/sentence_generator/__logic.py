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


def far_of(ci: CIValue):
    return CIValue(
        value=1 - 1/ci.value if ci.value and abs(ci.value) > 1e-15 else float('nan'),
        ql=1 - 1/ci.ql if ci.ql and abs(ci.value) > 1e-15 else float('nan'),
        qu=1 - 1/ci.qu if ci.qu and abs(ci.value) > 1e-15 else float('nan'),
    )


def build_metrics(stats, t):
    pF = extract_ci(stats, "pF", t)
    pC = extract_ci(stats, "pC", t)
    PR = extract_ci(stats, "PR", t)

    return Metrics(
        pF=pF,
        pC=pC,
        PR=PR,
        PR_inv=invert_ci(PR),
        FAR=far_of(PR),
        RP_F=extract_ci(stats, "RF", t),
        RP_C=extract_ci(stats, "RC", t),
    )