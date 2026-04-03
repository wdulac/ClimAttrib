from .__metrics import (
    probability,
    return_period,
    probability_ratio,
    fraction_of_attributable_risk,
    temperature
)


def unit_probability(value: float) -> str:
    return "%"


def unit_temperature(value: float) -> str:
    return "°C"


def unit_return_period(value: float) -> str:
    return "year" if value == 1 else "years"


def unit_ratio(value: float) -> str:
    return "time" if value == 1 else "times"


UNITS = {
    "probability": unit_probability,
    "temperature": unit_temperature,
    "return_period": unit_return_period,
    "ratio": unit_ratio,
}

FORMATTERS = {
    probability: unit_probability,
    return_period: unit_return_period,
    probability_ratio: unit_ratio,
    fraction_of_attributable_risk: unit_probability,
    temperature: unit_temperature,
}