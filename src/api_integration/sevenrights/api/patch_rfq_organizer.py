"""Not currently used

Смена организатора

Эндпоинт:

Смена организатора

Эндпоинт:

PATCH /api/v1/rfq/{id}/organizer

Authorization: Bearer {token}

Content-Type: application/json

Тело:

{

"user_id": 100407

}

user_id — активный пользователь вашей команды (справочник: GET /api/v1/rfq/team-users).

Ответ:

{

"id": 9798,

"creator_user": { "id": 100407, "name": "..." },

"organizer_name": "...",

"message": "Организатор успешно изменён"

}

PATCH /api/v1/rfq/{id}/organizer

Authorization: Bearer {token}

Content-Type: application/json

Тело:

{

"user_id": 100407

}

user_id — активный пользователь вашей команды (справочник: GET /api/v1/rfq/team-users).

Ответ:

{

"id": 9798,

"creator_user": { "id": 100407, "name": "..." },

"organizer_name": "...",

"message": "Организатор успешно изменён"

}

"""

import time
from pathlib import Path
import requests
from pydantic import ValidationError

from api_integration.constants import RFQ_DEFAULT_ORGANIZER_USER_ID
from api_integration.config import get_settings
from api_integration.sevenrights.api.schemas.rfq import RfqPatchOrganizerRequest
from api_integration.sevenrights.api.utils import _print_validation_errors


def patch_rfq_organizer(rfq_id: int, organizer_user_id: int, timeout: int = 30) -> dict:
    settings = get_settings()

    payload_data = {"organizer_user_id": organizer_user_id}

    try:
        model = RfqPatchOrganizerRequest.model_validate(payload_data)
    except ValidationError as exc:
        _print_validation_errors(exc)
        return {
            "error": f"ValidationError: {exc.errors()}",
            "rfq_id": None,
        }

    body = model.model_dump(mode="json", exclude_none=True)

    url = f"{settings.SEVEN_RIGHTS_API_URL.rstrip('/')}/rfq/{rfq_id}/organizer"

    headers = {
        "Authorization": f"Bearer {settings.SEVEN_RIGHTS_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.patch(url, headers=headers, json=body, timeout=timeout)
    except requests.RequestException as exc:
        return {
            "error": str(exc),
            "rfq_id": None,
        }

    if response.status_code == 200:
        try:
            _ = response.json()
        except ValueError:
            return {
                "error": "Invalid JSON in success response",
                "rfq_id": None,
            }

        return {
            "error": None,
            "rfq_id": rfq_id,
        }

    if response.status_code == 422:
        try:
            error_data = response.json()
        except ValueError:
            error_data = {}

        message = error_data.get("message", "Unknown validation error")
        errors = error_data.get("errors", {})

        return {
            "error": f"HTTP {response.status_code} ValidationError: {message} {errors}",
            "rfq_id": None,
        }

    return {
        "error": f"HTTP {response.status_code}: {response.text}",
        "rfq_id": None,
    }


if __name__ == "__main__":
    start_time = time.perf_counter()
    result = patch_rfq_organizer(
        rfq_id=9839,
        organizer_user_id=RFQ_DEFAULT_ORGANIZER_USER_ID,
        timeout=30,
    )
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(result)
    print(f"Request took {total_time:.6f} seconds to run")
