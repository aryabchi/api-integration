import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

from api_integration.constants import (
    ALLOWED_ATTACHMENT_FILE_EXTENSIONS,
    ALLOWED_ATTACHMENT_LOT_TEMPLATE_TERMS,
    ALLOWED_ATTACHMENT_RFQ_TEMPLATE_TERMS,
)
from api_integration.excel.rfq import (
    read_tender_excel,
    remap_excel_to_rfq_properties,
    apply_excel_value_mappings,
    merge_rfq_with_defaults,
)
from api_integration.excel.lot import read_lot_excel

logger = logging.getLogger(__name__)


@dataclass
class AttachmentTemplates:
    lot_template: list[str]
    rfq_template: list[str]


def find_attachment_templates(
    directory: Union[str, Path],
    extensions: tuple[str, ...] = ALLOWED_ATTACHMENT_FILE_EXTENSIONS,
) -> AttachmentTemplates:
    """
    Scans a directory for files with allowed extensions and classifies them
    as lot template or rfq template based on filename pattern matching.

    Args:
        directory: Path to the directory to search.
        extensions: Allowed file extensions (default from constants.py).

    Returns:
        AttachmentTemplates with lists of matching file names.
    """
    base = Path(directory)
    normalized_exts = tuple(ext.lower().lstrip(".") for ext in extensions)
    lot: list[str] = []
    rfq: list[str] = []

    if not base.is_dir():
        return AttachmentTemplates(lot_template=[], rfq_template=[])

    for path in sorted(base.iterdir()):
        if not path.is_file():
            continue
        if path.name.startswith("~$"):
            continue
        if path.suffix.lower().lstrip(".") not in normalized_exts:
            continue
        name = path.name.lower()
        if any(term in name for term in ALLOWED_ATTACHMENT_LOT_TEMPLATE_TERMS):
            lot.append(path.name)
        elif any(term in name for term in ALLOWED_ATTACHMENT_RFQ_TEMPLATE_TERMS):
            rfq.append(path.name)

    return AttachmentTemplates(lot_template=lot, rfq_template=rfq)


def validate_attachment_templates(templates: AttachmentTemplates) -> bool:
    """
    Validates AttachmentTemplates:
    - each list must contain exactly one file
    - file names must be different
    """
    if len(templates.lot_template) != 1 or len(templates.rfq_template) != 1:
        return False
    return templates.lot_template[0] != templates.rfq_template[0]


def process_attachments(
    directory: Union[str, Path],
    extensions: tuple[str, ...] = ALLOWED_ATTACHMENT_FILE_EXTENSIONS,
) -> dict[str, Any]:
    """
    End-to-end wrapper: find templates, validate, read lot and RFQ Excel, remap, merge.
    """
    result: dict[str, Any] = {"lot_template": None, "rfq_template": None, "error": []}

    try:
        templates = find_attachment_templates(directory, extensions)
        if not validate_attachment_templates(templates):
            exts = ", ".join(extensions)
            msg = (
                f"Attachments validation failed: must be two unique {exts} files. "
                f"Lot template filename should include one of: {', '.join(ALLOWED_ATTACHMENT_LOT_TEMPLATE_TERMS)}. "
                f"RFQ template filename should include one of: {', '.join(ALLOWED_ATTACHMENT_RFQ_TEMPLATE_TERMS)}."
            )
            logger.info(msg)
            result["error"] = [msg]
            return result

        if not templates.rfq_template:
            msg = "No RFQ template file found"
            logger.info(msg)
            result["error"] = [msg]
            return result

        if templates.lot_template:
            lot_path = Path(directory) / templates.lot_template[0]
            lot_result = read_lot_excel(lot_path)
            if "error" in lot_result:
                result["error"] = [lot_result["error"]]
                result["lot_template"] = None
            else:
                result["lot_template"] = lot_result

        rfq_path = Path(directory) / templates.rfq_template[0]
        rfq_data = read_tender_excel(rfq_path)
        if "error" in rfq_data:
            result["error"] = [rfq_data["error"]]
            return result

        rfq_data = remap_excel_to_rfq_properties(rfq_data)
        rfq_data = apply_excel_value_mappings(rfq_data)
        result["rfq_template"] = merge_rfq_with_defaults(rfq_data)

    except Exception as exc:
        result["error"] = [str(exc)]

    return result


def test_excel_pipeline() -> None:
    """Run process_attachments pipeline tests and print statistics."""
    import sys
    from api_integration.constants import SAMPLES_DIR

    samples_dir = Path(SAMPLES_DIR) / "excel"
    if not samples_dir.exists():
        print(f"Samples directory not found: {samples_dir}")
        sys.exit(1)

    print("=== Testing process_attachments pipeline ===")
    merged_data = process_attachments(samples_dir)
    print(f"lot_template: {'OK' if merged_data.get('lot_template') else 'None/Error'}")
    print(f"rfq_template: {'OK' if merged_data.get('rfq_template') else 'None/Error'}")
    print(f"error: {merged_data.get('error')}")

    with open(samples_dir / "rfq_excel.json", "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

    print("\n=== process_attachments result ===")
    print(json.dumps(merged_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_excel_pipeline()
