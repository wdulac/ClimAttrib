def format_prob(p: float) -> str:
    return f"{100*p:.3g}%"

def format_return_period(r: float) -> str:
    return f"{r:.0f} years"

def format_FAR(far: float) -> str:
    return f"{far:.1%}"

def format_PR(pr: float) -> str:
    return f"{pr:.1f}"

def format_year(y: int) -> str:
    return str(y)