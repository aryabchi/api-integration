from typing import Any
from api_integration.sevenrights.api.post_rfq import post_rfq
from api_integration.sevenrights.api.post_lot_template import post_lot_template
from api_integration.sevenrights.api.post_rfq_lot import post_rfq_lot
from api_integration.sevenrights.rfq.utils import split_rfq_payload
from api_integration.sevenrights.api.put_rfq_supplier_group_ids import (
    put_rfq_supplier_group_ids,
)


def create_rfq(rfq_data, timeout: int = 30) -> dict[str, Any]:
    """
    Implements complete RFQ creation piplene:
    - split payload
    - post RFQ draft
    - update draft with suppliers
    - load lot template
    - bind template to RFQ draft

    TODO:
    * declare returned dict keys
    * accumulate errors in "error", don't overwrite
    * pass payload.lot_template to post_lot_template
    """

    payload = split_rfq_payload(rfq_data)
    print("    -> Creaitng RFQ draft...")
    result = post_rfq(data=payload.rfq_template, timeout=timeout)

    if result.get("error") is None and payload.rfq_suppliers is not None:
        print("    -> Adding supplier groups to RFQ...")
        put_result = put_rfq_supplier_group_ids(
            rfq_id=result["rfq_id"],
            data=payload.rfq_suppliers,
            timeout=timeout,
        )
        if put_result.get("error") is not None:
            result["error"] = put_result["error"]

    # Handle lot template if present in payload (only if RFQ was created)
    if result.get("rfq_id") is not None and payload.lot_template:
        # Upload lot template (function decides: upload file or use default ID)
        print("    -> Importing lot template...")
        lot_result = post_lot_template(
            data=payload.lot_template,
            timeout=timeout,
        )
        if lot_result.get("error") is not None:
            result["error"] = lot_result["error"]
            return result
        lot_template_id = lot_result["lot_template_id"]

        # Bind lot template to RFQ (only if we have a valid ID)
        if lot_template_id is not None:
            print("    -> Binding lot template to RFQ...")
            lot_bind_result = post_rfq_lot(
                rfq_id=result["rfq_id"],
                lot_template_id=lot_template_id,
                timeout=timeout,
            )
            if lot_bind_result.get("error") is not None:
                result["error"] = lot_bind_result["error"]

    return result
