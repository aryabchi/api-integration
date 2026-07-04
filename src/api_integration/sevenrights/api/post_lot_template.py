"""Импорт матрицы лота

Файл Excel в формате 7RightsMatrix.xlsx (шаблон: /ваш путь/matrix-lot.xlsx).

POST /api/v1/rfq/lot-templates/import

Authorization: Bearer {token}
Content-Type: multipart/form-data
file: matrix-lot.xlsx
response sample:
{
  "data": {
    "id": 13197,
    "lot_template_id": 13197,
    "title": "20260701_1701_example_matrix-lot.xlsx"
  }
}
Сохраните lot_template_id — он понадобится при создании RFQ.
"""

from pathlib import Path
from typing import Any

import requests

from api_integration.config import get_settings
from api_integration.sevenrights.api.schemas.api_results import LotTemplateApiResult


def post_lot_template(
    data: dict[str, Any] | None = None,
    timeout: int = 30,
) -> LotTemplateApiResult:
    """
    Post an Excel file as a new lot template via multipart/form-data upload.
    Implements POST /api/v1/rfq/lot-templates/import
    Returns:
        LotTemplateApiResult: dict with keys "error" and "lot_template_id"
    """

    settings = get_settings()

    if not data:
        return {
            "error": "Missing lot_template data",
            "lot_template_id": None,
        }

    file_path = Path(data.get("path", ""))
    default_lot_template_id = data.get("lot_template_id")
    if not file_path.exists():
        return {
            "error": f"File not found: {file_path}",
            "lot_template_id": None,
        }

    url = f"{settings.SEVEN_RIGHTS_API_URL.rstrip('/')}/rfq/lot-templates/import"

    headers = {
        "Authorization": f"Bearer {settings.SEVEN_RIGHTS_API_KEY}",
    }

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
    except (requests.exceptions.RequestException, OSError) as exc:
        return {
            "error": str(exc),
            "lot_template_id": None,
        }

    try:
        response_json = response.json()
    except ValueError:
        return {
            "error": f"HTTP {response.status_code}: Invalid JSON response",
            "lot_template_id": None,
        }

    if response.status_code == 201:
        lot_template_id_from_response = response_json.get("data", {}).get(
            "lot_template_id"
        )
        if lot_template_id_from_response:
            lot_template_id = lot_template_id_from_response
        else:
            lot_template_id = default_lot_template_id

        if lot_template_id is None:
            return {
                "error": "Missing lot_template_id in response and no default provided",
                "lot_template_id": None,
            }

        return {
            "error": None,
            "lot_template_id": lot_template_id,
        }

    return {
        "error": f"HTTP {response.status_code}: {response.text}",
        "lot_template_id": None,
    }
