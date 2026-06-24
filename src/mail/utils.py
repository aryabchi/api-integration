import sys
from pathlib import Path

src_path = str(Path(__file__).resolve().parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from constants import RFQ_DRAFT_LINK


def get_valid_rfq_draft_link(rfq_id: int, template: str = RFQ_DRAFT_LINK) -> str:
    return template.format(rfq_id=rfq_id)


if __name__ == "__main__":
    # Test cases
    rfq_id = 1325984

    print(get_valid_rfq_draft_link(rfq_id))
