import sys
from pathlib import Path
import json
import requests

src_path = str(Path(__file__).resolve().parent.parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from constants import SAMPLES_DIR
from config import get_settings


def get_rfq_lot(
    base_url: str,
    rfq_id: int,
    bearer_token: str,
    company_id: int | None = None,
    is_actual: int | None = None,
    output_root: str = SAMPLES_DIR,
    timeout: int = 30,
):
    """
    Get lots for an existing RFQ.
    Implements GET /api/v1/rfq/{rfq_id}/lot
    """
    base = f"{base_url.rstrip('/')}/rfq/{rfq_id}/lot"
    params = {}
    if company_id is not None:
        params["company_id"] = company_id
    if is_actual is not None:
        params["is_actual"] = is_actual

    url = base
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json",
    }

    print("=" * 80)
    print(f"Request URL : {url}")
    print(f"RFQ ID      : {rfq_id}")
    if company_id is not None:
        print(f"Company ID  : {company_id}")
    if is_actual is not None:
        print(f"Is Actual   : {is_actual}")
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
        tmp_dir = Path(output_root)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        response_file = tmp_dir / "response_detail.html"
        with open(response_file, "w", encoding="utf-8") as f:
            f.write(response.text)
            sys.exit(1)

    if response.status_code == 200:
        print("SUCCESS: RFQ lots retrieved.")

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

    print("\nFULL RESPONSE JSON")
    print("=" * 80)
    print(json.dumps(response_json, indent=2, ensure_ascii=False))

    tmp_dir = Path(output_root) / str(rfq_id)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    response_file = tmp_dir / "lot_detail.json"

    with open(response_file, "w", encoding="utf-8") as f:
        json.dump(response_json, f, indent=2, ensure_ascii=False)

    print("\nSaved response to:")
    print(response_file.resolve())

    print("\nRFQ LOT DETAIL OBJECT")
    print("=" * 80)

    if isinstance(response_json, dict):
        for key, value in response_json.items():
            print(f"{key}:")
            print(json.dumps(value, indent=2, ensure_ascii=False))
            print()

    if not response.ok:
        sys.exit(1)

    return response_json


if __name__ == "__main__":
    settings = get_settings()
    get_rfq_lot(
        base_url=settings.SEVEN_RIGHTS_API_URL,
        rfq_id=9876,
        bearer_token=settings.SEVEN_RIGHTS_API_KEY,
        company_id=None,
        is_actual=1,
    )
