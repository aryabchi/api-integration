"""Тестовый модуль привязка к RFQ шаблона лота

### Привязка шаблона к RFQ через lot_template_id

Да. lot_template_id — это id из GET /lot-templates (запись в customed_rfq_lots).

Важно: при привязке шаблон копируется (создаётся экземпляр лота для RFQ). Исходный шаблон остается в справочнике.

Способы привязки:

    При создании RFQ — POST /api/v1/rfq с полем lot_template_id.
    После создания — POST /api/v1/rfq/{id}/lot с телом {"lot_template_id": 12345} (только если у RFQ ещё нет лота).
    Обновление — PUT /api/v1/rfq/{id} с lot_template_id (только если customed_lot_id ещё пустой).

В ответе на GET /api/v1/rfq/{id} привязанный лот — поле customed_lot_id (это уже копия, не id шаблона).

Типовой сценарий API:

1. GET /api/v1/rfq/lot-templates → выбрать id шаблона

2. POST /api/v1/rfq { ..., lot_template_id }

или

POST /api/v1/rfq { ... }

POST /api/v1/rfq/{id}/lot { lot_template_id }

3. GET /api/v1/rfq/{id}/lot → структура и данные лота


### Что такое «данные лота» для PUT /api/v1/rfq/{id}/lot/data

Это не создание шаблона и не первичная загрузка организатором таблицы направлений при создании RFQ в ЛК.

PUT /api/v1/rfq/{id}/lot/data — сохранение предложения перевозчика (или черновика) по редактируемым колонкам лота: цена, гарантия, поля ввода и т.п. Аналог действия перевозчика в таблице лота в ЛК.

Тело запроса:

Поле


Описание

is_actual


0 — черновик, 1 — актуальное/поданное предложение

data


JSON-строка с массивом листов (формат как у GET /rfq/{id}/lot, после фильтрации)

company_id


опционально — firma_id перевозчика (по умолчанию — компания текущего пользователя)

language


опционально — ru / en

В data попадают только колонки типов:

    Цена
    Гарантия
    Поле ввода
    Числовое поле ввода

(как в LOT_EDITABLE_COLUMN_TYPES API).

Рекомендуемый порядок: GET /api/v1/rfq/{id}/lot → изменить нужные ячейки → передать результат в PUT .../lot/data.
"""

import sys
from pathlib import Path
import json
import requests

from api_integration.constants import SAMPLES_DIR
from api_integration.config import get_settings


def post_rfq_lot(
    base_url: str,
    rfq_id: int,
    bearer_token: str,
    lot_data: dict,
    output_root: str = SAMPLES_DIR,
    timeout: int = 30,
):
    """
    Post lot data to an existing RFQ.
    Implements POST /api/v1/rfq/{rfq_id}/lot
    """
    url = f"{base_url.rstrip('/')}/rfq/{rfq_id}/lot"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    print("=" * 80)
    print(f"Request URL : {url}")
    print(f"RFQ ID      : {rfq_id}")
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
        print("SUCCESS: RFQ lot posted.")

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

    response_file = tmp_dir / "lot_post_response.json"

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

    post_rfq_lot(
        base_url=settings.SEVEN_RIGHTS_API_URL,
        rfq_id=rfq_id,
        bearer_token=settings.SEVEN_RIGHTS_API_KEY,
        lot_data=lot_data,
    )
