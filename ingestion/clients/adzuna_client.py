import os
from .base_client import get_with_retries

BASE_URL = "https://api.adzuna.com/v1/api/jobs"

def fetch_postings(what=None, where=None, max_pages=1, results_per_page=50):
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    country = os.getenv("ADZUNA_COUNTRY", "us")

    if not app_id or not app_key:
        raise RuntimeError("ADZUNA_APP_ID / ADZUNA_APP_KEY not set in .env")

    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}/{country}/search/{page}"
        params = {"app_id": app_id, "app_key": app_key, "results_per_page": results_per_page}
        if what:
            params["what"] = what
        if where:
            params["where"] = where

        data = get_with_retries(url, params=params)
        results = data.get("results", [])
        if not results:
            break
        for job in results:
            yield job

def external_id(job: dict) -> str:
    return str(job["id"])