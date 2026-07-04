"""GET /api/v1/rfq/lot-templates

### Как найти id шаблона — GET /api/v1/rfq/lot-templates

Параметры запроса:

Параметр


Обязательный


Описание

rfq_id


нет


Если передан — вернёт лот, уже привязанный к этому RFQ (0 или 1 элемент). Если лот не привязан — {"data":[]}.

Параметров поиска (search, фильтр по названию и т.п.) сейчас нет.

Без rfq_id метод возвращает список свободных шаблонов команды: шаблоны team_id текущего пользователя, которые ещё не привязаны ни к одному RFQ (new_lot_id).

Формат ответа:

{

"data": [

{ "id": 12345, "name": "Название шаблона" }

]

}

    id — идентификатор для lot_template_id
    name — поле title шаблона в БД

Как искать шаблон: получить полный список и отфильтровать по name на стороне клиента. Если шаблон уже использован в другом RFQ, он не попадёт в список — тогда нужен новый шаблон (копия в ЛК) или привязка через rfq_id уже созданной процедуры.

Сортировка: по title (названию), по возрастанию.
"""

import sys
from pathlib import Path
import json
import requests

from api_integration.constants import SAMPLES_DIR
from api_integration.config import get_settings


def get_lot_templates(
    base_url: str,
    bearer_token: str,
    rfq_id: int = None,
    output_root: str = SAMPLES_DIR,
    timeout: int = 30,
):
    """
    Get lot templates.
    Implements GET /api/v1/rfq/lot-templates

    Args:
        base_url: Base URL of the API
        bearer_token: Authentication token
        rfq_id: Optional RFQ ID. If provided, returns lot template bound to this RFQ.
                If not provided, returns list of free team templates.
        output_root: Root directory for saving responses
        timeout: Request timeout in seconds
    """
    url = f"{base_url.rstrip('/')}/rfq/lot-templates"

    # Add rfq_id as query parameter if provided
    if rfq_id is not None:
        url = f"{url}?rfq_id={rfq_id}"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json",
    }

    print("=" * 80)
    print(f"Request URL : {url}")
    if rfq_id is not None:
        print(f"RFQ ID      : {rfq_id}")
    else:
        print("RFQ ID      : (not specified - fetching all free templates)")
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

    #
    # Handle common HTTP statuses
    #
    if response.status_code == 200:
        print("SUCCESS: Lot templates retrieved.")

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

    #
    # Print complete response body
    #
    print("\nFULL RESPONSE JSON")
    print("=" * 80)
    print(json.dumps(response_json, indent=2, ensure_ascii=False))

    #
    # Save response
    #
    tmp_dir = Path(output_root)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    response_file = tmp_dir / "lot_templates.json"

    with open(response_file, "w", encoding="utf-8") as f:
        json.dump(response_json, f, indent=2, ensure_ascii=False)

    print("\nSaved response to:")
    print(response_file.resolve())

    #
    # Fail script on non-success HTTP status
    #
    if not response.ok:
        sys.exit(1)

    return response_json


if __name__ == "__main__":
    settings = get_settings()

    # Example: fetch all free lot templates (no rfq_id)
    # To fetch lot template for specific RFQ, pass rfq_id parameter
    get_lot_templates(
        base_url=settings.SEVEN_RIGHTS_API_URL,
        bearer_token=settings.SEVEN_RIGHTS_API_KEY,
        rfq_id=None,  # 9903,  # Uncomment to fetch template for specific RFQ
    )
