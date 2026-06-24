from datetime import date, datetime
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class RfqCreateRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    # Required
    title: str = Field(..., max_length=255)
    finish_datetime: datetime

    # Optional
    income_id: str | None = None
    name_for_human: str | None = None
    requirements: str | None = None

    late_submission_datetime: datetime | None = None

    contract_start_date: date | None = None
    contract_end_date: date | None = None

    access_type: Literal["all", "selected", "groups"] | None = None

    is_for_all: bool = False

    lot_template_id: int | None = None

    type_view: Literal[1, 2, 3] | None = None

    traffic_light_type: int | None = None

    prolongacia: bool = False
    max_date_prolongacia: datetime | None = None

    can_questions: bool = True

    finish_message: str | None = None
    change_message: str | None = None

    transport_type_ids: List[int] = Field(default_factory=list)

    supplier_company_ids: List[int] = Field(default_factory=list)

    supplier_emails: List[str] = Field(default_factory=list)

    contacts: List[int] = Field(default_factory=list)

    user_access_ids: List[int] = Field(
        default_factory=list,
        description="Users allowed to edit the RFQ",
    )
