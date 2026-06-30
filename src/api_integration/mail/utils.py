from api_integration.constants import RFQ_DRAFT_URL


def get_rfq_draft_url(rfq_id: int, template: str = RFQ_DRAFT_URL) -> str:
    return template.format(rfq_id=rfq_id)


if __name__ == "__main__":
    # Test cases
    rfq_id = 1325984

    print(get_rfq_draft_url(rfq_id))
