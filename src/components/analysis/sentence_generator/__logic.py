def should_include_today_phrase(event_year: int, now_year: int) -> bool:
    return event_year < now_year - 5