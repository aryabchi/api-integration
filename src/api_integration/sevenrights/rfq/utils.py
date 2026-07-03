from dataclasses import dataclass
from typing import Any

from api_integration.constants import IS_SKIP_PUT_RFQ_SUPPLIER_GROUP_IDS
from api_integration.sevenrights.api.schemas.rfq import RfqUpdateSupplierGroupIdsRequest


@dataclass
class RfqPayload:
    lot_template: dict[str, Any] | None
    rfq_template: dict[str, Any]
    rfq_suppliers: dict[str, Any] | None


def split_rfq_payload(
    rfq_excel_data: dict[str, Any],
    skip_frq_supplier_groups: bool = IS_SKIP_PUT_RFQ_SUPPLIER_GROUP_IDS,
) -> RfqPayload:
    """
    Splits RFQ_EXCEL_MARKER JSON into lot_template, rfq_template and rfq_suppliers.

    Args:
        rfq_excel_data: JSON returned by process_attachments from excel_reader.py.
        skip_frq_supplier_groups: If True, rfq_suppliers is None (PUT call is skipped).
            If False, rfq_suppliers contains {"access_type": ..., "supplier_group_ids": [...]}.

    Returns:
        RfqPayload with separated fields. access_type and supplier_group_ids are ALWAYS
        removed from rfq_template regardless of skip_frq_supplier_groups flag.
    """
    lot_template = rfq_excel_data.get("lot_template", {})
    rfq_template = dict(rfq_excel_data.get("rfq_template", {}))

    # Extract fields defined in RfqUpdateSupplierGroupIdsRequest schema
    supplier_fields = set(RfqUpdateSupplierGroupIdsRequest.model_fields.keys())
    rfq_suppliers = {}
    for field in supplier_fields:
        rfq_suppliers[field] = rfq_template.pop(field, None)

    if skip_frq_supplier_groups:
        return RfqPayload(
            lot_template=lot_template,
            rfq_template=rfq_template,
            rfq_suppliers=None,
        )
    else:
        return RfqPayload(
            lot_template=lot_template,
            rfq_template=rfq_template,
            rfq_suppliers=rfq_suppliers,
        )
