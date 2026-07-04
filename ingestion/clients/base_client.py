import time
import requests

class ApiRequestError(Exception):
    pass

def get_with_retries(url, params=None, headers=None, max_retries=3, timeout=15, backoff_seconds=2):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)

            if response.status_code == 429:
                time.sleep(backoff_seconds * attempt * 2)
                last_error = f"429 rate limited (attempt {attempt})"
                continue

            if 500 <= response.status_code < 600:
                time.sleep(backoff_seconds * attempt)
                last_error = f"{response.status_code} server error (attempt {attempt})"
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            last_error = str(e)
            time.sleep(backoff_seconds * attempt)

    raise ApiRequestError(f"Failed after {max_retries} attempts. Last error: {last_error}")