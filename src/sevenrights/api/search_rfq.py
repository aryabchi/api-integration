import sys
import time
import requests
from pathlib import Path

src_path = str(Path(__file__).resolve().parent.parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from config import get_settings


def search_rfq(title: str, timeout: int = 30) -> dict:
    settings = get_settings()

    url = f"{settings.SEVEN_RIGHTS_API_URL.rstrip('/')}/rfq"

    headers = {
        "Authorization": f"Bearer {settings.SEVEN_RIGHTS_API_KEY}",
        "Accept": "application/json",
    }

    params = {"search": title, "page": 1, "perPage": 50}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
    except requests.RequestException as exc:
        return {
            "error": str(exc),
            "rfq_id": None,
        }

    if response.status_code == 401:
        try:
            error_data = response.json()
        except ValueError:
            error_data = {}

        message = error_data.get("message", "Unauthorized")
        return {
            "error": f"HTTP {response.status_code}: {message}",
            "rfq_id": None,
        }

    if response.status_code != 200:
        return {
            "error": f"HTTP {response.status_code}: {response.text}",
            "rfq_id": None,
        }

    try:
        data = response.json()
    except ValueError:
        return {
            "error": "Invalid JSON in success response",
            "rfq_id": None,
        }

    items = data.get("data") or []
    if not items:
        return {
            "error": None,
            "rfq_id": None,
        }

    rfq_id = items[0].get("id")
    return {
        "error": None,
        "rfq_id": rfq_id,
    }


if __name__ == "__main__":
    start_time = time.perf_counter()
    query = "АВТО - Артем - Хабаровский край - 08.07.2026 - 01.09.2026"
    print(f"Searching for: {query}")
    res = search_rfq(query)
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(res)
    print(f"Request took {total_time:.6f} seconds to run")

    start_time = time.perf_counter()
    query = "test non existing rfq title 123"
    print(f"\nSearching for: {query}")
    res2 = search_rfq(query)
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(res2)
    print(f"Request took {total_time:.6f} seconds to run")
