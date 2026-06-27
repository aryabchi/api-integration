import sys
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Union

try:
    from openpyxl import load_workbook
except ImportError as exc:
    raise ImportError("openpyxl is required to read Excel files") from exc

src_path = str(Path(__file__).resolve().parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

    from constants import (
        ALLOWED_ATTACHMENT_FILE_EXTENSIONS,
        ALLOWED_ATTACHMENT_LOT_TEMPLATE_TERMS,
        ALLOWED_ATTACHMENT_RFQ_TEMPLATE_TERMS,
        EXCEL_TO_RFQ_MAPPING,
        EXCEL_TO_RFQ_VALUES_MAPPING,
        RFQ_TO_DEFAULTS_MAPPING,
    )
from sevenrights.api.schemas.rfq import RfqCreateRequest


@dataclass
class AttachmentTemplates:
    lot_template: List[str]
    rfq_template: List[str]


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
    lot: List[str] = []
    rfq: List[str] = []

    if not base.is_dir():
        return AttachmentTemplates(lot_template=[], rfq_template=[])

    for path in sorted(base.iterdir()):
        if not path.is_file():
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
    sheet_name: str = "TENDER",
) -> dict[str, Any]:
    """
    End-to-end wrapper: find templates, validate, read RFQ Excel, remap, merge.
    Skips lot_template processing for now (TODO).
    """
    templates = find_attachment_templates(directory, extensions)
    if not validate_attachment_templates(templates):
        msg = "Attachment validation failed: each template type must have exactly one unique file"
        print(msg)
        return {"error": msg}

    # TODO: implement lot_template processing

    if not templates.rfq_template:
        msg = "No RFQ template file found"
        print(msg)
        return {"error": msg}

    try:
        rfq_path = Path(directory) / templates.rfq_template[0]
        data = read_tender_excel(rfq_path, sheet_name=sheet_name)
        if "error" in data:
            return data

        rfq_data = remap_excel_to_rfq_properties(data)
        rfq_data = apply_excel_value_mappings(rfq_data)
        return merge_rfq_with_defaults(rfq_data)
    except Exception as exc:
        return {"error": str(exc)}


def read_tender_excel(
    path: Union[str, Path], sheet_name: str = "TENDER"
) -> dict[str, str]:
    """
    Reads an Excel file, extracts data from the specified sheet,
    and returns a dictionary with keys from column A and values
    from column C (fallback to column B if C is empty/None).

    Args:
        path: Path to the Excel file (.xlsx, .xls, etc.)
        sheet_name: Name of the sheet to read (default: "TENDER")

    Returns:
        dict with str keys and str values, or {"error": "..."} if sheet is missing.
    """

    wb = load_workbook(path, data_only=True)
    if sheet_name not in wb.sheetnames:
        msg = f"Sheet '{sheet_name}' not found in {path}. Available sheets: {wb.sheetnames}"
        print(msg)
        return {"error": msg}

    ws = wb[sheet_name]
    result: dict[str, str] = {}

    for row in ws.iter_rows(min_row=2, values_only=True):
        key = row[0] if row and len(row) > 0 else None
        col_b = row[1] if row and len(row) > 1 else None
        col_c = row[2] if row and len(row) > 2 else None

        if key is None:
            continue

        key_str = str(key).strip()
        if not key_str:
            continue

        value = col_c if (col_c is not None and str(col_c).strip() != "") else col_b
        result[key_str] = str(value).strip() if value is not None else ""

    return result


def apply_excel_value_mappings(data: dict[str, str]) -> dict[str, Any]:
    """
    Converts raw Excel string values to API-valid types using EXCEL_TO_RFQ_VALUES_MAPPING.

    For each key in data, if the key exists in EXCEL_TO_RFQ_VALUES_MAPPING and the value
    matches a known Excel value, it is replaced with the corresponding API value.
    If no exact match is found, the value is split by ';' and each part is mapped
    individually (unmapped parts are excluded). If at least one part is mapped:
    - all mapped values are lists -> flattened into a single list
    - otherwise -> single value if one mapped part, else list of mapped values
    If the input contains an 'error' key, returns a dict with only the error.

    Args:
        data: Dictionary with RFQ property names and raw Excel string values.

    Returns:
        Dictionary with converted values, or {'error': ...} if input contains an error.
    """
    if "error" in data:
        return {"error": data["error"]}

    result: dict[str, Any] = {}
    for key, value in data.items():
        if key not in EXCEL_TO_RFQ_VALUES_MAPPING:
            result[key] = value
            continue

        mapping = EXCEL_TO_RFQ_VALUES_MAPPING[key]
        if value in mapping:
            result[key] = mapping[value]
            continue

        parts = [part.strip() for part in value.split(";")]
        mapped_parts: list[Any] = []
        for part in parts:
            if part in mapping:
                mapped_parts.append(mapping[part])

        if not mapped_parts:
            result[key] = value
        else:
            if all(isinstance(v, list) for v in mapped_parts):
                result[key] = [item for sublist in mapped_parts for item in sublist]
            else:
                result[key] = (
                    mapped_parts[0] if len(mapped_parts) == 1 else mapped_parts
                )

    # Type coercion for known numeric fields
    if "freight_spend_of_event" in result and isinstance(
        result["freight_spend_of_event"], str
    ):
        if result["freight_spend_of_event"].isdigit():
            result["freight_spend_of_event"] = int(result["freight_spend_of_event"])

    return result


def remap_excel_to_rfq_properties(data: dict[str, str]) -> dict[str, str]:
    """
    Remaps dictionary keys from Excel field names to RFQ request property names
    using EXCEL_TO_RFQ_MAPPING from constants.py.

    Args:
        data: Dictionary returned by read_tender_excel()

    Returns:
        New dictionary with remapped keys where mapping exists.
        If input contains 'error', it is retained in the output.
    """
    result = {
        rfq_key: data[excel_key]
        for excel_key, rfq_key in EXCEL_TO_RFQ_MAPPING.items()
        if excel_key in data
    }
    if "error" in data:
        result["error"] = data["error"]
    return result


def merge_rfq_with_defaults(data: dict[str, str]) -> dict[str, str]:
    """
    Merges the remapped RFQ dictionary with RFQ_TO_DEFAULTS_MAPPING from constants.py.
    Missing fields are added from defaults; overlapping keys take precedence from defaults.
    If the input contains an 'error' key, returns a dict with only the error.

    Args:
        data: Dictionary returned by remap_excel_to_rfq_properties()

    Returns:
        Merged dictionary, or {'error': ...} if input contains an error.
    """
    if "error" in data:
        return {"error": data["error"]}

    merged = dict(data)
    merged.update(RFQ_TO_DEFAULTS_MAPPING)
    return merged


if __name__ == "__main__":
    import sys

    default_path = (
        Path(__file__).resolve().parent.parent.parent
        / "samples"
        / "excel"
        / "Шаблон запроса создания тендера v1.3.xlsx"
        # / "Шаблон запроса создания тендера v1.2.xlsx"
        # / "Шаблон запроса создания тендера v1.3_remarks.xlsx"
    )
    file_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path

    if not Path(file_path).exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    data = read_tender_excel(file_path)
    print("=== Raw Excel data ===")
    print(json.dumps(data, ensure_ascii=False, indent=2))

    rfq_data = remap_excel_to_rfq_properties(data)
    print("\n=== Remapped RFQ properties ===")
    print(json.dumps(rfq_data, ensure_ascii=False, indent=2))

    rfq_data = apply_excel_value_mappings(rfq_data)
    print("\n=== RFQ values converted ===")
    print(json.dumps(rfq_data, ensure_ascii=False, indent=2))

    merged_data = merge_rfq_with_defaults(rfq_data)
    print("\n=== Merged RFQ with defaults ===")
    print(
        json.dumps(
            merged_data,
            ensure_ascii=False,
            indent=2,
        )
    )

    try:
        validated = RfqCreateRequest.model_validate(merged_data)
        print("\n=== Pydantic validation ===")
        print("OK:", validated.model_dump(mode="json", exclude_none=True))
    except Exception as exc:
        print("\n=== Pydantic validation ===")
        print("FAILED:", exc)

    # test process_attachments
    print("\n=== Attachments reading ===")
    path = (
        Path(__file__).resolve().parent.parent.parent
        # / "downloads"
        # / "233431782309822@mail.yandex.ru"
        / "samples"
        / "excel"
    )
    merged_data = process_attachments(path)
    print("\n=== process_attachments result ===")
    print(json.dumps(merged_data, ensure_ascii=False, indent=2))
    with open(path / "rfq_excel.json", "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
