from science import compute_event_stats

def event_stats(event):
    """
    Dummy dynamic component that returns part of the output of the attribution
    calculation
    """
    stats = compute_event_stats(event)
    # Timeseries of the best-estimate for pC, pF and PR
    out = stats.loc[:, 'BE', :] 
    return out