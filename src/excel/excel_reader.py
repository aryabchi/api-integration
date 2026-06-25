import sys
import json
from pathlib import Path
from typing import Union

try:
    from openpyxl import load_workbook
except ImportError as exc:
    raise ImportError("openpyxl is required to read Excel files") from exc

src_path = str(Path(__file__).resolve().parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from constants import (
    EXCEL_TO_RFQ_MAPPING,
    RFQ_TO_DEFAULTS_MAPPING,
)
from sevenrights.api.schemas.rfq import RfqCreateRequest


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
