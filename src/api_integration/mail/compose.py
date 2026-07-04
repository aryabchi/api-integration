import os
import json

from api_integration.constants import (
    DOWNLOADS_DIR,
    SUCCESS_REPLY_TEMPLATE,
    ERROR_REPLY_TEMPLATE,
    PARTIAL_SUCCESS_REPLY_TEMPLATE,
    RFQ_INFO_MARKER,
    RFQ_EXCEL_MARKER,
    REPLY_BODY_MARKER,
)
from api_integration.mail.utils import get_rfq_draft_url


def _normalize_error(error) -> list[str]:
    """Normalize error field to list[str] format (backward compat)."""
    if error is None:
        return []
    if isinstance(error, str):
        return [error]
    if isinstance(error, list):
        return error
    return [str(error)]


def _extract_nested_value(data: dict = None, key_path: str = "") -> str:
    """Safely extract a value from nested dict using slash-separated path.

    Args:
        data: Dictionary to extract from
        key_path: Slash-separated path (e.g., "rfq_template/requirements")

    Returns:
        str: Extracted value converted to string, or empty string if path invalid
    """
    if not data or not isinstance(data, dict) or not key_path:
        return ""

    keys = key_path.split("/")
    current = data

    for key in keys[:-1]:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
        if current is None:
            return ""

    if not isinstance(current, dict):
        return ""

    value = current.get(keys[-1], "")
    return str(value) if value is not None else ""


def _compose_reply_text(
    meta: dict,
    body: str,
    body_excerpt_chars: int = 500,
    rfq_info: dict = None,
    rfq_excel: dict = None,
    extra_on_success_rfq_excel_key_path: str = "",
) -> str:
    """Fills in email templates depending on rfq_info fields content

    Returns:
        str: filled email template
    """
    subject = meta.get("subject", "") or ""
    subject_line = f' "{subject}" ' if subject else " "
    error_list = _normalize_error(rfq_info.get("error")) if rfq_info else []
    error_message = "; ".join(error_list)
    rfq_id = rfq_info.get("rfq_id", 0) if rfq_info else 0

    # Extract extra value from rfq_excel using the provided key path
    extra_on_success = _extract_nested_value(
        rfq_excel, extra_on_success_rfq_excel_key_path
    )

    if error_message and rfq_id:
        template = PARTIAL_SUCCESS_REPLY_TEMPLATE
        message = get_rfq_draft_url(rfq_id)
        warning = error_message
        return template.format(
            subject_line=subject_line,
            date=meta.get("date", "unknown date"),
            body_excerpt=body[:body_excerpt_chars].strip() or "(empty body)",
            message=message,
            warning=warning,
            extra_on_success=extra_on_success,
        )
    elif error_message:
        template = ERROR_REPLY_TEMPLATE
        message = error_message
    elif rfq_id:
        template = SUCCESS_REPLY_TEMPLATE
        message = get_rfq_draft_url(rfq_id)
    else:
        template = ERROR_REPLY_TEMPLATE
        message = "(unable to generate rfq link or error message)"

    return template.format(
        # sender_name=_extract_sender_name(meta.get("from", "")),
        subject_line=subject_line,
        date=meta.get("date", "unknown date"),
        body_excerpt=body[:body_excerpt_chars].strip() or "(empty body)",
        message=message,
        extra_on_success=extra_on_success if rfq_id else "",
    )


# def _extract_sender_name(from_field: str) -> str:
#     """
#     'John Doe <john@example.com>' -> 'John Doe', fallback to local part.
#     TODO: fix for non-unicode encoding
#     """
#     m = re.match(r'^"?([^"<]*)"?\s*<', from_field or "")
#     if m and m.group(1).strip():
#         return m.group(1).strip()
#     m = re.search(r"<([^>]+)>", from_field or "")
#     addr = m.group(1) if m else (from_field or "").strip()
#     return addr.split("@")[0] if addr else "there"


def generate_replies(
    download_dir: str = DOWNLOADS_DIR,
    body_excerpt_chars: int = 500,
    exclude: tuple = ("junk",),
    subfolder: str | None = None,
    dry_run: bool = False,
    test_run: bool = False,
) -> int:
    """Generate a ``reply.txt`` inside every email subfolder using a template.
    Skips generation if ``reply.txt`` already exists in the subfolder.

    Parameters
    ----------
    download_dir:
        Root directory produced by fetch_mail.
    reply_template:
        Python format-string with placeholders {sender_name}, {subject_line},
        {date}, {body_excerpt}. Defaults to DEFAULT_REPLY_TEMPLATE.
    body_excerpt_chars:
        How many characters of the original body to include in the template.
    exclude:
        Tuple of folder names to exclude from processing.
    subfolder:
        Process only this specific subfolder instead of all folders.
    dry_run:
        If True, print actions without writing files.
    test_run:
        If True, overwrite existing reply file. If False, skip existing.
    """
    if subfolder:
        folder_path = os.path.join(download_dir, subfolder)
        if not os.path.isdir(folder_path):
            print(f"✗ Subfolder not found: {folder_path}")
            return 0
        folders_to_process = [folder_path]
    else:
        if not os.path.isdir(download_dir):
            print(f"Download directory not found: {download_dir}")
            return 0
        folders_to_process = [
            os.path.join(download_dir, entry)
            for entry in sorted(os.listdir(download_dir))
            if os.path.isdir(os.path.join(download_dir, entry)) and entry not in exclude
        ]

    generated = 0
    skipped = 0

    for folder_path in folders_to_process:
        entry = os.path.basename(folder_path)

        meta_path = os.path.join(folder_path, "email_meta.json")
        body_path = os.path.join(folder_path, "email_body.txt")
        reply_path = os.path.join(folder_path, REPLY_BODY_MARKER)

        if not os.path.exists(meta_path):
            continue

        # Skip if reply file already exists (unless test_run mode)
        if os.path.exists(reply_path) and not test_run:
            print(f"  -> Skipping (reply already exists): {entry}")
            skipped += 1
            continue

        # Skip if RFQ marker is missing in this email directory
        marker_path = os.path.join(folder_path, RFQ_INFO_MARKER)
        rfq_excel_path = os.path.join(folder_path, RFQ_EXCEL_MARKER)

        # Initialize variables
        rfq_info = None
        rfq_excel = None

        # Check RFQ_INFO_MARKER first (regular case with rfq_id from search_rfq/create_rfq)
        if os.path.exists(marker_path):
            with open(marker_path, "r", encoding="utf-8") as f:
                rfq_info = json.load(f)

        # Read RFQ_EXCEL_MARKER if it exists (needed for requirements extraction and error checking)
        if os.path.exists(rfq_excel_path):
            with open(rfq_excel_path, "r", encoding="utf-8") as f:
                rfq_excel = json.load(f)
            # Normalize error field (backward compat: old files may have str or None)
            if "error" in rfq_excel:
                rfq_excel["error"] = _normalize_error(rfq_excel["error"])
            # Use error from rfq_excel only if no RFQ_INFO_MARKER present
            if rfq_excel.get("error") and rfq_info is None:
                rfq_info = {
                    "error": rfq_excel["error"],
                    "rfq_id": None,
                }

        # If still no rfq_info (neither marker exists or excel has no error), skip
        if rfq_info is None:
            print(f"  -> Skipping (no RFQ info marker): {entry}")
            skipped += 1
            continue

        if dry_run:
            print(f"  [dry-run] would generate reply for: {entry}")
            generated += 1
            continue

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        body = ""
        if os.path.exists(body_path):
            with open(body_path, "r", encoding="utf-8") as f:
                body = f.read()

        reply_text = _compose_reply_text(
            meta=meta,
            body=body,
            body_excerpt_chars=body_excerpt_chars,
            rfq_info=rfq_info,
            rfq_excel=rfq_excel,
            extra_on_success_rfq_excel_key_path="rfq_template/requirements",
        )

        with open(reply_path, "w", encoding="utf-8") as f:
            f.write(reply_text)

        print(f"  ✓ reply generated for: {entry}")
        generated += 1

    print(f"\nTotal replies generated: {generated}")
    print(f"Total replies skipped: {skipped}")
    return generated
