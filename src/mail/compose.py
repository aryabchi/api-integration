import os
import re
import json
from constants import (
    DOWNLOADS_DIR,
    DEFAULT_REPLY_TEMPLATE,
    RFQ_DRAFT_LINK,
)


def _extract_sender_name(from_field: str) -> str:
    """'John Doe <john@example.com>' -> 'John Doe', fallback to local part."""
    m = re.match(r'^"?([^"<]*)"?\s*<', from_field or "")
    if m and m.group(1).strip():
        return m.group(1).strip()
    m = re.search(r"<([^>]+)>", from_field or "")
    addr = m.group(1) if m else (from_field or "").strip()
    return addr.split("@")[0] if addr else "there"


def generate_replies(
    download_dir: str = DOWNLOADS_DIR,
    reply_template: str = None,
    body_excerpt_chars: int = 500,
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
    """
    if not os.path.isdir(download_dir):
        print(f"Download directory not found: {download_dir}")
        return 0

    template = reply_template or DEFAULT_REPLY_TEMPLATE
    generated = 0
    skipped = 0

    for entry in sorted(os.listdir(download_dir)):
        folder_path = os.path.join(download_dir, entry)
        if not os.path.isdir(folder_path):
            continue

        meta_path = os.path.join(folder_path, "email_meta.json")
        body_path = os.path.join(folder_path, "email_body.txt")
        reply_path = os.path.join(folder_path, "reply.txt")

        if not os.path.exists(meta_path):
            continue

        # --- Skip if reply file already exists ---
        if os.path.exists(reply_path):
            print(f"  -> Skipping (reply.txt already exists): {entry}")
            skipped += 1
            continue

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        body = ""
        if os.path.exists(body_path):
            with open(body_path, "r", encoding="utf-8") as f:
                body = f.read()

        # Template formatting
        subject = meta.get("subject", "") or ""
        subject_line = f' "{subject}" ' if subject else " "
        reply_text = template.format(
            sender_name=_extract_sender_name(meta.get("from", "")),
            subject_line=subject_line,
            date=meta.get("date", "unknown date"),
            body_excerpt=body[:body_excerpt_chars].strip() or "(empty body)",
            rfq_link=RFQ_DRAFT_LINK or "(unable to generate valid link)",
        )

        with open(reply_path, "w", encoding="utf-8") as f:
            f.write(reply_text)

        print(f"  ✓ reply generated for: {entry}")
        generated += 1

    print(f"\nTotal replies generated: {generated}")
    print(f"Total replies skipped (already exist): {skipped}")
    return generated
