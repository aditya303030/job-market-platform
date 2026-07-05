CURRENCY_BY_COUNTRY = {
    "us": "USD", "gb": "GBP", "ca": "CAD", "au": "AUD",
    "de": "EUR", "fr": "EUR", "nl": "EUR", "in": "INR",
}


def parse_adzuna_salary(payload: dict, country: str) -> dict:
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


def parse_usajobs_salary(descriptor: dict) -> dict:
    """USAJOBS returns a LIST of pay ranges (PositionRemuneration) since one
    posting can span multiple grades. We take the widest overall range."""
    ranges = descriptor.get("PositionRemuneration") or []

    mins, maxes = [], []
    for r in ranges:
        try:
            mins.append(float(r.get("MinimumRange", 0) or 0))
            maxes.append(float(r.get("MaximumRange", 0) or 0))
        except (TypeError, ValueError):
            continue

    return {
        "salary_min": min(mins) if mins else None,
        "salary_max": max(maxes) if maxes else None,
        "currency": "USD",
        "salary_is_predicted": False,  # federal postings always disclose real ranges
    }