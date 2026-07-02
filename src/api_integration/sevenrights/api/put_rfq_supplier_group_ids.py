import time
import requests
from pydantic import ValidationError

from api_integration.config import get_settings
from api_integration.sevenrights.api.schemas.rfq import RfqUpdateSupplierGroupIdsRequest
from api_integration.sevenrights.api.utils import _print_validation_errors


def put_rfq_supplier_group_ids(rfq_id: int, data: dict, timeout: int = 30) -> dict:
    settings = get_settings()

    payload_data = data

    try:
        model = RfqUpdateSupplierGroupIdsRequest.model_validate(payload_data)
    except ValidationError as exc:
        _print_validation_errors(exc)
        return {
            "error": f"ValidationError: {exc.errors()}",
            "rfq_id": rfq_id,
        }

    body = model.model_dump(mode="json", exclude_none=True)

    url = f"{settings.SEVEN_RIGHTS_API_URL.rstrip('/')}/rfq/{rfq_id}"

    headers = {
        "Authorization": f"Bearer {settings.SEVEN_RIGHTS_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.put(url, headers=headers, json=body, timeout=timeout)
    except requests.RequestException as exc:
        return {
            "error": str(exc),
            "rfq_id": rfq_id,
        }

    if response.status_code == 200:
        try:
            _ = response.json()
        except ValueError:
            return {
                "error": "Invalid JSON in success response",
                "rfq_id": rfq_id,
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
            "rfq_id": rfq_id,
        }

    return {
        "error": f"HTTP {response.status_code}: {response.text}",
        "rfq_id": rfq_id,
    }


if __name__ == "__main__":
    start_time = time.perf_counter()
    result = put_rfq_supplier_group_ids(
        rfq_id=9842,
        timeout=180,
        data={
            "access_type": "groups",
            "supplier_group_ids": [29, 36],
        },
    )
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(result)
    print(f"Request took {total_time:.6f} seconds to run")
