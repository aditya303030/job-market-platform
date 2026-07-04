CURRENCY_BY_COUNTRY = {
    "us": "USD", "gb": "GBP", "ca": "CAD", "au": "AUD",
    "de": "EUR", "fr": "EUR", "nl": "EUR", "in": "INR",
}

def parse_salary(payload: dict, country: str) -> dict:
    salary_min = payload.get("salary_min")
    salary_max = payload.get("salary_max")
    is_predicted = bool(payload.get("salary_is_predicted", 0))
    currency = CURRENCY_BY_COUNTRY.get(country.lower(), "USD")

    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        salary_min, salary_max = salary_max, salary_min

    return {
        "salary_min": salary_min,
        "salary_max": salary_max,
        "currency": currency,
        "salary_is_predicted": is_predicted,
    }