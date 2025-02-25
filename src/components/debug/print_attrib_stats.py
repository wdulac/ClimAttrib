from science import compute_event_stats

def event_stats(event):
    stats, *_ = compute_event_stats(event)

    test = stats.loc[1994, 'BE', :]

    return test