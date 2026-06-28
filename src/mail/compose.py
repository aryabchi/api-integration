import os
import json
from constants import (
    DOWNLOADS_DIR,
    SUCCESS_REPLY_TEMPLATE,
    ERROR_REPLY_TEMPLATE,
    RFQ_INFO_MARKER,
    REPLY_BODY_MARKER,
)
from mail.utils import get_rfq_draft_url


def _compose_reply_text(
    meta: dict,
    body: str,
    body_excerpt_chars: int = 500,
    rfq_info: dict = None,
) -> str:
    subject = meta.get("subject", "") or ""
    subject_line = f' "{subject}" ' if subject else " "
    """Fills in email templates depending on rfq_info fields content
    TODO: consider case (and use 3rd template) when rfq_info "error" and "rfq_id" both not null 

    Returns:
        str: filled email template
    """
    if not rfq_info:
        template = ERROR_REPLY_TEMPLATE
        message = "(unable to generate rfq link or error message)"
    else:
        error_message = rfq_info.get("error", "")
        if error_message:
            template = ERROR_REPLY_TEMPLATE
            message = error_message
        else:
            template = SUCCESS_REPLY_TEMPLATE
            rfq_id = rfq_info.get("rfq_id", 0)
            if rfq_id:
                message = get_rfq_draft_url(rfq_id)
            else:
                message = "(unable to generate valid RFQ link)"

    return template.format(
        # sender_name=_extract_sender_name(meta.get("from", "")),
        subject_line=subject_line,
        date=meta.get("date", "unknown date"),
        body_excerpt=body[:body_excerpt_chars].strip() or "(empty body)",
        message=message,
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

        reply_text = _compose_reply_text(
            meta=meta,
            body=body,
            body_excerpt_chars=body_excerpt_chars,
            rfq_info=rfq_info,
        )

        with open(reply_path, "w", encoding="utf-8") as f:
            f.write(reply_text)

        print(f"  ✓ reply generated for: {entry}")
        generated += 1

    print(f"\nTotal replies generated: {generated}")
    print(f"Total replies skipped: {skipped}")
    return generated
