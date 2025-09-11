def should_include_today_update(event_year: int, now_year: int) -> bool:
    return event_year < now_year - 5


def should_mention_FAR(FAR_then):
    return FAR_then > 0