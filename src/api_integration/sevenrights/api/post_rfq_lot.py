"""Привязка к RFQ шаблона лота

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
# sample response_json
# {"rfq_id": 9949, "customed_lot_id": 13201, "lot_template_id": 13200}

3. GET /api/v1/rfq/{id}/lot → структура и данные лота
"""

import requests

from api_integration.config import get_settings
from api_integration.sevenrights.api.schemas.api_results import LotBindingApiResult


def post_rfq_lot(
    rfq_id: int,
    lot_template_id: int,
    timeout: int = 30,
) -> LotBindingApiResult:
    """
    Bind a lot template to an existing RFQ.
    Implements POST /api/v1/rfq/{rfq_id}/lot
    Returns:
        LotBindingApiResult: dict with keys "error" and "customed_lot_id"
    """

    settings = get_settings()

    url = f"{settings.SEVEN_RIGHTS_API_URL.rstrip('/')}/rfq/{rfq_id}/lot"

    headers = {
        "Authorization": f"Bearer {settings.SEVEN_RIGHTS_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {"lot_template_id": lot_template_id}

    try:
        response = requests.post(
            url,
            headers=headers,
            json=body,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return {
            "customed_lot_id": None,
            "error": str(exc),
        }

    try:
        response_json = response.json()

    except ValueError:
        return {
            "customed_lot_id": None,
            "error": "Invalid JSON in response",
        }

    if response.status_code in (200, 201):
        return {
            "customed_lot_id": response_json.get("customed_lot_id"),
            "error": None,
        }

    return {
        "customed_lot_id": None,
        "error": f"HTTP {response.status_code}: {response.text}",
    }


if __name__ == "__main__":
    import time

    start_time = time.perf_counter()
    result = post_rfq_lot(
        rfq_id=9949,
        lot_template_id=13200,
    )
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(result)
    print(f"Request took {total_time:.6f} seconds to run")
