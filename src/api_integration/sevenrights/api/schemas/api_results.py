from typing import Optional, TypedDict


class RfqResult(TypedDict):
    """Return type for RFQ creation and update operations."""

    error: Optional[str]
    rfq_id: Optional[int]


class LotTemplateResult(TypedDict):
    """Return type for lot template import operations."""

    error: Optional[str]
    lot_template_id: Optional[int]


class LotBindingResult(TypedDict):
    """Return type for lot binding to RFQ operations."""

    error: Optional[str]
    customed_lot_id: Optional[int]
