import time
import os
from .base_client import get_with_retries

BASE_URL = "https://data.usajobs.gov/api/search"


def _headers():
    auth_key = os.getenv("USAJOBS_AUTH_KEY")
    user_agent = os.getenv("USAJOBS_USER_AGENT")
    if not auth_key or not user_agent:
        raise RuntimeError("USAJOBS_AUTH_KEY / USAJOBS_USER_AGENT not set in .env")
    return {"Host": "data.usajobs.gov", "User-Agent": user_agent, "Authorization-Key": auth_key}


def fetch_postings(keyword=None, location=None, max_pages=1, results_per_page=25):
    headers = _headers()
    for page in range(1, max_pages + 1):
        params = {"ResultsPerPage": results_per_page, "Page": page}
        if keyword:
            params["Keyword"] = keyword
        if location:
            params["LocationName"] = location

        data = get_with_retries(BASE_URL, params=params, headers=headers)
        items = data.get("SearchResult", {}).get("SearchResultItems", [])
        if not items:
            break
        for item in items:
            yield item

        time.sleep(0.5)


def external_id(job: dict) -> str:
    return str(job["MatchedObjectId"])