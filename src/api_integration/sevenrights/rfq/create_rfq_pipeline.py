import time

from api_integration.sevenrights.api.post_rfq import post_rfq
from api_integration.sevenrights.rfq.utils import split_rfq_payload
from api_integration.sevenrights.api.put_rfq_supplier_group_ids import (
    put_rfq_supplier_group_ids,
)


def create_rfq(rfq_data, timeout: int = 30, debug: bool = False):
    """Split payload, post RFQ template, and attach supplier groups if available."""
    payload = split_rfq_payload(rfq_data)
    # TODO: use payload.lot_template for lot-related operations

    print("  -> Creaitng RFQ...")
    start_time = time.time() if debug else None
    result = post_rfq(data=payload.rfq_template, timeout=timeout)
    if debug:
        elapsed = time.time() - start_time
        print(f"     post_rfq execution time: {elapsed:.2f}s")

    if result.get("error") is None and payload.rfq_suppliers is not None:
        print("  -> Adding supplier groups to RFQ...")
        start_time = time.time() if debug else None
        put_result = put_rfq_supplier_group_ids(
            rfq_id=result["rfq_id"],
            data=payload.rfq_suppliers,
            timeout=timeout,
        )
        if debug:
            elapsed = time.time() - start_time
            print(f"     put_rfq_supplier_group_ids execution time: {elapsed:.2f}s")
        if put_result.get("error") is not None:
            result = put_result

    return result
