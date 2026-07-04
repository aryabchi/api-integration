from typing import Optional, TypedDict


class RfqApiResult(TypedDict):
    """Inner API result type (single error string)."""

    error: Optional[str]
    rfq_id: Optional[int]


class RfqResult(TypedDict):
    """Pipeline result type (accumulated errors as list)."""

    error: Optional[list[str]]
    rfq_id: Optional[int]


class LotTemplateApiResult(TypedDict):
    """Return type for lot template import operations."""

    error: Optional[str]
    lot_template_id: Optional[int]


class LotBindingApiResult(TypedDict):
    """Return type for lot binding to RFQ operations."""

    error: Optional[str]
    customed_lot_id: Optional[int]
