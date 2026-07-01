"""Не поддерживается API v1

### Первый шаг — создание шаблона в ЛК

Первый шаг сценария — подготовка шаблона лота (customed_rfq_lots) в личном кабинете, раздел «Шаблоны»:

    «+ Добавить шаблон» — визуальный конструктор (структура листов, столбцов, строк, типы колонок).
    «Импорт Excel» — загрузка Excel в шаблон (**POST /admin/customedRfqLots/importing**);
    создаётся запись шаблона с разобранной структурой и исходными значениями ячеек.

На текущий момент создание и редактирование шаблона через API v1 не предусмотрено — только через ЛК (или внутренние web-эндпоинты).
API работает с уже существующими шаблонами.
"""

import sys
from pathlib import Path
import json
import requests

from api_integration.constants import SAMPLES_DIR
from api_integration.config import get_settings


def post_lot_template(
    base_url: str,
    bearer_token: str,
    lot_data: dict,
    output_root: str = SAMPLES_DIR,
    timeout: int = 30,
):
    """
    Post lot data as a new lot template.
    Implements POST /api/v1/rfq/lot-templates
    """
    url = f"{base_url.rstrip('/')}/rfq/lot-templates"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    print("=" * 80)
    print(f"Request URL : {url}")
    print(f"Payload size: {len(json.dumps(lot_data, ensure_ascii=False))} chars")
    print("=" * 80)

    try:
        response = requests.post(
            url,
            headers=headers,
            json=lot_data,
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
        sys.exit(1)

    return response_json


if __name__ == "__main__":
    settings = get_settings()

    rfq_id = 9876
    lot_json_path = Path(SAMPLES_DIR) / str(rfq_id) / "lot_detail.json"

    if not lot_json_path.exists():
        print(f"ERROR: Lot JSON not found at {lot_json_path}")
        sys.exit(1)

    with open(lot_json_path, "r", encoding="utf-8") as f:
        lot_data = json.load(f)

    post_lot_template(
        base_url=settings.SEVEN_RIGHTS_API_URL,
        bearer_token=settings.SEVEN_RIGHTS_API_KEY,
        lot_data=lot_data,
    )
