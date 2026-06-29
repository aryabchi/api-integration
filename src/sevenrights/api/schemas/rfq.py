from datetime import date, datetime
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class UserAccessItem(BaseModel):
    """Validation model for user_access RFQ property"""

    user_id: int = Field(..., description="The unique identifier for the user")
    access_type: int = Field(..., description="The type level of access granted")


class RfqCreateRequest(BaseModel):
    """Validation model for RFQ"""

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

    participant_access_type: Literal[0, 1, 2] | None = None

    freight_spend_of_event: int | None = 1
    freight_spend_currency_id: int | None = 1

    # обратная связь
    type_view: Literal[0, 1, 2, 3] | None = None
    traffic_light_type: Literal[0, 1] | None = None
    traffic_light_price_type: Literal[0, 1, 2] | None = None
    show_best_price: bool | None = False
    price_green_finish_percent: int | None = Field(default=None, ge=0, le=100)
    price_yellow_finish_percent: int | None = Field(default=None, ge=0, le=100)

    prolongacia: bool = False
    max_date_prolongacia: datetime | None = None

    can_questions: bool = True

    finish_message: str | None = None
    change_message: str | None = None

    transport_type_ids: List[int] = Field(default_factory=list)

    supplier_company_ids: List[int] = Field(default_factory=list)
    supplier_group_ids: List[int] = Field(default_factory=list)

    supplier_emails: List[str] = Field(default_factory=list)

    contact_ids: List[int] = Field(default_factory=list)

    # user_access_ids: List[int] = Field(
    #     default_factory=list,
    #     description="Users allowed to edit the RFQ",
    # ) # obsolete, replace with user_access
    user_access: list[UserAccessItem]

    is_ban_on_price_increases_on_this_tour: bool | None = True
    is_invite_link_enabled: bool | None = True


class RfqUpdateSupplierGroupIdsRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    access_type: Literal["groups"] = "groups"
    supplier_group_ids: List[int] = Field(default_factory=list)


class RfqPatchOrganizerRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    organizer_user_id: int
