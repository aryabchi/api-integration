"""Тестовый модуль получение RFQ"""

import sys
from pathlib import Path
import json
import requests

from api_integration.constants import SAMPLES_DIR
from api_integration.config import get_settings


def get_rfq(
    base_url: str,
    rfq_id: int,
    bearer_token: str,
    output_root: str = SAMPLES_DIR,
    timeout: int = 30,
):
    """Get existing RFQ. Implements getRfq API contract"""
    url = f"{base_url.rstrip('/')}/rfq/{rfq_id}"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json",
    }

    print("=" * 80)
    print(f"Request URL : {url}")
    print(f"RFQ ID      : {rfq_id}")
    print("=" * 80)

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
        )

    except requests.exceptions.Timeout:
        print("ERROR: Request timed out.")
        sys.exit(1)

    except requests.exceptions.ConnectionError as e:
        print("ERROR: Connection failed.")
        print(str(e))
        sys.exit(1)

    except requests.exceptions.RequestException as e:
        print("ERROR: Unexpected request failure.")
        print(str(e))
        sys.exit(1)

    print(f"HTTP Status: {response.status_code}")

    try:
        response_json = response.json()
    except ValueError:
        print("ERROR: Response is not valid JSON.")
        print("\nRaw response:")
        # print(response.text[:256])
        tmp_dir = Path(output_root)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        response_file = tmp_dir / "response_detail.html"
        with open(response_file, "w", encoding="utf-8") as f:
            # save full page
            f.write(response.text)
            sys.exit(1)

    #
    # Handle common HTTP statuses
    #
    if response.status_code == 200:
        print("SUCCESS: RFQ retrieved.")

    elif response.status_code == 400:
        print("ERROR: Bad Request (400)")

    elif response.status_code == 401:
        print("ERROR: Unauthorized (401)")
        print("Check bearer token.")

    elif response.status_code == 403:
        print("ERROR: Forbidden (403)")

    elif response.status_code == 404:
        print(f"ERROR: RFQ {rfq_id} not found (404)")

    elif response.status_code >= 500:
        print(f"ERROR: Server error ({response.status_code})")

    else:
        print(f"WARNING: Unexpected status code {response.status_code}")

    #
    # Print complete response body
    #
    print("\nFULL RESPONSE JSON")
    print("=" * 80)
    print(json.dumps(response_json, indent=2, ensure_ascii=False))

    #
    # Save response
    #
    tmp_dir = Path(output_root) / str(rfq_id)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    response_file = tmp_dir / "rfq_detail.json"

    with open(response_file, "w", encoding="utf-8") as f:
        json.dump(response_json, f, indent=2, ensure_ascii=False)

    print("\nSaved response to:")
    print(response_file.resolve())

    #
    # If API returns RfqDetail directly,
    # print all fields in a readable way.
    #
    print("\nRFQ DETAIL OBJECT")
    print("=" * 80)

    if isinstance(response_json, dict):
        for key, value in response_json.items():
            print(f"{key}:")
            print(json.dumps(value, indent=2, ensure_ascii=False))
            print()

    #
    # Fail script on non-success HTTP status
    #
    if not response.ok:
        sys.exit(1)

    return response_json


if __name__ == "__main__":
    settings = get_settings()
    rfq_id = 9924

    get_rfq(
        base_url=settings.SEVEN_RIGHTS_API_URL,
        rfq_id=rfq_id,
        bearer_token=settings.SEVEN_RIGHTS_API_KEY,
    )
