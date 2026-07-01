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


def _extract_requirements(rfq_excel: dict = None) -> str:
    """Extract 'requirements' from rfq_excel nested structure."""
    if not rfq_excel or not isinstance(rfq_excel, dict):
        return ""
    rfq_template = rfq_excel.get("rfq_template")
    if not rfq_template or not isinstance(rfq_template, dict):
        return ""
    return rfq_template.get("requirements", "")


def _compose_reply_text(
    meta: dict,
    body: str,
    body_excerpt_chars: int = 500,
    rfq_info: dict = None,
    extra_on_success: str = "",
) -> str:
    subject = meta.get("subject", "") or ""
    subject_line = f' "{subject}" ' if subject else " "
    """Fills in email templates depending on rfq_info fields content

    Returns:
        str: filled email template
    """
    error_message = rfq_info.get("error", "") if rfq_info else ""
    rfq_id = rfq_info.get("rfq_id", 0) if rfq_info else 0

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
    subfolder: str = None,
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
        if not os.path.exists(marker_path):
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

        rfq_info = None
        if os.path.exists(marker_path):
            with open(marker_path, "r", encoding="utf-8") as f:
                rfq_info = json.load(f)

        rfq_excel = None
        rfq_excel_path = os.path.join(folder_path, RFQ_EXCEL_MARKER)
        if os.path.exists(rfq_excel_path):
            with open(rfq_excel_path, "r", encoding="utf-8") as f:
                rfq_excel = json.load(f)

        reply_text = _compose_reply_text(
            meta=meta,
            body=body,
            body_excerpt_chars=body_excerpt_chars,
            rfq_info=rfq_info,
            extra_on_success=_extract_requirements(rfq_excel),
        )

        with open(reply_path, "w", encoding="utf-8") as f:
            f.write(reply_text)

        print(f"  ✓ reply generated for: {entry}")
        generated += 1

    print(f"\nTotal replies generated: {generated}")
    print(f"Total replies skipped: {skipped}")
    return generated
