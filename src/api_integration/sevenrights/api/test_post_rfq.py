"""Временный модуль pydantic валидации json запросов на создание RFQ к API"""

from pathlib import Path
from datetime import datetime
import json
from pydantic import ValidationError

from api_integration.constants import (
    SAMPLES_DIR,
    TEST_RFQ_CREATE_TEMPLATE,
)
from api_integration.sevenrights.api.schemas.rfq import RfqCreateRequest
from api_integration.sevenrights.api.utils import _print_validation_errors

if __name__ == "__main__":
    try:
        rfq1 = RfqCreateRequest(
            title="Transport RFQ 2026-001",
            finish_datetime=datetime.fromisoformat("2026-07-15T12:00:00+00:00"),
            requirements="Temperature-controlled transport required.",
            access_type="selected",
            type_view=1,
            supplier_company_ids=[101, 102, 103],
            supplier_emails=[
                "vendor1@example.com",
                "vendor2@example.com",
            ],
            transport_type_ids=[5, 7],
            contacts=[42],
            user_access_ids=[42, 43],
        )

        payload = rfq1.model_dump(mode="json", exclude_none=True)
        print(payload)

        rfq2 = RfqCreateRequest(
            title="Transport RFQ 2026-001" * 42,
            finish_datetime=datetime.fromisoformat("2026-07-15 12:00:00"),
            requirements="Temperature-controlled transport required.",
            access_type="smth_else",
            type_view=1,
            supplier_company_ids=[101, 102, 103],
            supplier_emails=[
                "vendor1@example.com",
                "vendor2@example.com",
            ],
            transport_type_ids=[5, 7],
            contacts=[42],
            user_access_ids=[42, 43],
            additional_field="42",
        )
        payload = rfq2.model_dump(mode="json", exclude_none=True)
        print(payload)

    except ValidationError as e:
        _print_validation_errors(e)

    try:
        data = json.loads(Path(SAMPLES_DIR, "rfq1.json").read_text(encoding="utf-8"))
        rfq3 = RfqCreateRequest.model_validate(data)

    except ValidationError as exc:
        _print_validation_errors(exc)

    payload = rfq3.model_dump(
        mode="json",
        exclude_none=True,
    )

    print("Payload ready for API:")
    print(payload)
