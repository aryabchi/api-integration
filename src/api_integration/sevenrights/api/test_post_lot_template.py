"""Тестовый модуль импорт матрицы лота

Файл Excel в формате 7RightsMatrix.xlsx (шаблон: /ваш путь/matrix-lot.xlsx).

POST /api/v1/rfq/lot-templates/import

Authorization: Bearer {token}

Content-Type: multipart/form-data


file: matrix-lot.xlsx

Ответ:

{

"data": {

"id": ХХХХХ,

"lot_template_id": ХХХХХ,

"title": "matrix-lot.xlsx"

}

}

Сохраните lot_template_id — он понадобится при создании RFQ.
"""

from pathlib import Path
import json
import requests

from api_integration.constants import SAMPLES_DIR
from api_integration.config import get_settings


def post_lot_template(
    base_url: str,
    bearer_token: str,
    file_path: str | Path,
    output_root: str = SAMPLES_DIR,
    timeout: int = 30,
):
    """
    Post an Excel file as a new lot template via multipart/form-data upload.
    Implements POST /api/v1/rfq/lot-templates/import
    """
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return None

    url = f"{base_url.rstrip('/')}/rfq/lot-templates/import"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
    }

    print("=" * 80)
    print(f"Request URL : {url}")
    print(f"Upload file : {file_path.name} ({file_path.stat().st_size} bytes)")
    print("=" * 80)

    try:
        with open(file_path, "rb") as f:
            files = {
                "file": (
                    file_path.name,
                    f,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            }
            response = requests.post(
                url,
                headers=headers,
                files=files,
                timeout=timeout,
            )
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out.")
        return None

    except requests.exceptions.ConnectionError as e:
        print("ERROR: Connection failed.")
        print(str(e))
        return None

    except requests.exceptions.RequestException as e:
        print("ERROR: Unexpected request failure.")
        print(str(e))
        return None

    except OSError as e:
        print(f"ERROR: Failed to read file: {e}")
        return None

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
        return None

    if response.status_code in (200, 201):
        print("SUCCESS: Lot template posted.")

    elif response.status_code == 400:
        print("ERROR: Bad Request (400)")

    elif response.status_code == 401:
        print("ERROR: Unauthorized (401)")
        print("Check bearer token.")

    elif response.status_code == 403:
        print("ERROR: Forbidden (403)")

    elif response.status_code == 404:
        print("ERROR: Endpoint not found (404)")

    elif response.status_code >= 500:
        print(f"ERROR: Server error ({response.status_code})")

    else:
        print(f"WARNING: Unexpected status code {response.status_code}")

    print("\nFULL RESPONSE JSON")
    print("=" * 80)
    print(json.dumps(response_json, indent=2, ensure_ascii=False))

    response_file = Path(output_root) / "lot_template_post_response.json"

    with open(response_file, "w", encoding="utf-8") as f:
        json.dump(response_json, f, indent=2, ensure_ascii=False)

    print("\nSaved response to:")
    print(response_file.resolve())

    if not response.ok:
        return None

    return response_json


if __name__ == "__main__":
    settings = get_settings()

    file_path = Path(SAMPLES_DIR) / "excel" / "20260701_1701_example_matrix-lot.xlsx"

    post_lot_template(
        base_url=settings.SEVEN_RIGHTS_API_URL,
        bearer_token=settings.SEVEN_RIGHTS_API_KEY,
        file_path=file_path,
    )
