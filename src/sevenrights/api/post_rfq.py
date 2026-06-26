from re import U
import sys
from pathlib import Path
import requests
from pydantic import ValidationError

src_path = str(Path(__file__).resolve().parent.parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from constants import TEST_RFQ_CREATE_BOILERPLATE
from config import get_settings
from sevenrights.api.schemas.rfq import RfqCreateRequest


def _print_validation_errors(exc: ValidationError) -> None:
    print("\nVALIDATION FAILED")
    print("=" * 80)

    for idx, error in enumerate(exc.errors(), start=1):
        field = ".".join(str(x) for x in error["loc"])
        message = error["msg"]
        error_type = error["type"]

        print(f"[{idx}] Field : {field}")
        print(f"    Type  : {error_type}")
        print(f"    Error : {message}")
        print()

    print("=" * 80)


def create_rfq(data: dict = None) -> dict:
    settings = get_settings()

    payload_data = data if data is not None else TEST_RFQ_CREATE_BOILERPLATE

    try:
        model = RfqCreateRequest.model_validate(payload_data)
    except ValidationError as exc:
        _print_validation_errors(exc)
        return {
            "error": f"ValidationError: {exc.errors()}",
            "rfq_id": None,
        }

    body = model.model_dump(mode="json", exclude_none=True)

    url = f"{settings.SEVEN_RIGHTS_API_URL.rstrip('/')}/rfq"

    headers = {
        "Authorization": f"Bearer {settings.SEVEN_RIGHTS_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
    except requests.RequestException as exc:
        return {
            "error": str(exc),
            "rfq_id": None,
        }

    if response.status_code == 201:
        try:
            response_data = response.json()
        except ValueError:
            return {
                "error": "Invalid JSON in success response",
                "rfq_id": None,
            }

        rfq_id = response_data.get("id")
        if rfq_id is None:
            return {
                "error": "Missing 'id' in success response",
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
            "error": f"ValidationError: {message} {errors}",
            "rfq_id": None,
        }

    return {
        "error": f"HTTP {response.status_code}: {response.text}",
        "rfq_id": None,
    }


if __name__ == "__main__":
    result = create_rfq(
        data={
            "title": "Тестовая закупка транспортных услуг",
            "finish_datetime": "2026-07-01T18:00:00Z",
        }
    )
    print(result)
