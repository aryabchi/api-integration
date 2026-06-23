"""Helper Functions"""

import os
import re
import json
import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mail.sanitizers import sanitize_filename
from constants import (
    DOWNLOADS_DIR,
    ALLOWED_ATTACHMENT_FILE_EXTENSIONS,
    IMAP_MAIL_SEARCH_TEMPLATE,
    DEFAULT_REPLY_TEMPLATE,
    RFQ_DRAFT_LINK,
)


def decode_mime_filename(filename_header):
    """Decodes MIME encoded-word syntax in filenames."""
    if not filename_header:
        return None

    decoded_fragments = decode_header(filename_header)
    decoded_filename = ""

    for fragment, charset in decoded_fragments:
        if isinstance(fragment, bytes):
            # Decode bytes to string using the specified charset (fallback to utf-8)
            decoded_filename += fragment.decode(charset or "utf-8", errors="ignore")
        else:
            decoded_filename += fragment

    return decoded_filename


def _unique_path(base_path: str) -> str:
    """Append _1, _2, ... if a path already exists."""
    if not os.path.exists(base_path):
        return base_path
    counter = 1
    root, ext = os.path.splitext(base_path)
    # For directories ext is empty, so just append to root
    while True:
        candidate = f"{root}_{counter}{ext}"
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def fetch_mail(
    imap_server: str,
    imap_port: int,
    mailbox: str,
    password: str,
    imap_mail_search_template: str = IMAP_MAIL_SEARCH_TEMPLATE,
    download_dir: str = DOWNLOADS_DIR,
    allowed_attachment_extensions: tuple = ALLOWED_ATTACHMENT_FILE_EXTENSIONS,
) -> None:
    """Connects to mailbox, searches for relevant emails and saves their
    attachments into per-email subfolders.

    Layout produced::

        download_dir/
            <sanitized_subject>/
                email_meta.json   # sender, subject, message-id, date, ...
                email_body.txt    # plain-text body (or HTML fallback)
                attachment1.xlsx
                attachment2.xlsx
                ...
    """

    os.makedirs(download_dir, exist_ok=True)
    mail = None
    try:
        print(f"Connecting to {imap_server}...")
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)

        print("Logging in...")
        mail.login(mailbox, password)
        mail.select("INBOX")

        print(f"Searching for emails by pattern: '{imap_mail_search_template}'...")
        status, messages = mail.search(None, imap_mail_search_template)

        if status != "OK":
            print("No emails found or search failed.")
            return

        email_ids = messages[0].split()
        print(f"Found {len(email_ids)} matching email(s).")

        attachments_saved = 0

        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")

            for response_part in msg_data:
                if not isinstance(response_part, tuple):
                    continue

                msg = email.message_from_bytes(response_part[1])

                # --- Decode subject ---
                subject_raw, charset = decode_header(msg["Subject"])[0]
                if isinstance(subject_raw, bytes):
                    subject = subject_raw.decode(charset or "utf-8", errors="ignore")
                else:
                    subject = subject_raw or ""

                print(f"\nProcessing email: {subject or '(no subject)'}")

                # --- Build per-email subfolder ---
                folder_name = sanitize_filename(subject) if subject else ""
                if not folder_name:
                    folder_name = f"No_Subject_{e_id.decode()}"
                email_folder_path = _unique_path(
                    os.path.join(download_dir, folder_name)
                )
                os.makedirs(email_folder_path, exist_ok=True)

                # --- Persist metadata ---
                metadata = {
                    "email_id": e_id.decode(),
                    "subject": subject,
                    "from": msg.get("From", ""),
                    "to": msg.get("To", ""),
                    "message_id": msg.get("Message-ID", ""),
                    "date": msg.get("Date", ""),
                    "folder": os.path.basename(email_folder_path),
                }
                with open(
                    os.path.join(email_folder_path, "email_meta.json"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)

                # --- Extract body (prefer text/plain) ---
                body_text, body_html = "", ""
                for part in msg.walk():
                    ctype = part.get_content_type()
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue
                    charset = part.get_content_charset() or "utf-8"
                    decoded = payload.decode(charset, errors="ignore")
                    if ctype == "text/plain" and not body_text:
                        body_text = decoded
                    elif ctype == "text/html" and not body_html:
                        body_html = decoded

                with open(
                    os.path.join(email_folder_path, "email_body.txt"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(body_text or body_html)

                # --- Save attachments ---
                for part in msg.walk():
                    filename_raw = part.get_filename()
                    if not filename_raw:
                        continue

                    filename = decode_mime_filename(filename_raw)
                    filename = sanitize_filename(filename)
                    if not filename:
                        continue

                    base, ext = os.path.splitext(filename)
                    if ext.lower() not in allowed_attachment_extensions:
                        continue  # skip non-excel attachment

                    filepath = _unique_path(os.path.join(email_folder_path, filename))

                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))

                    print(f"  -> Saved: {os.path.basename(filepath)}")
                    attachments_saved += 1

        print(f"\nDone! Total attachments saved: {attachments_saved}")

    except imaplib.IMAP4.error as e:
        print(f"IMAP Error: {e}")
        print(
            "Hints:\n"
            "- Ensure you are using an App Password, not regular Yandex password.\n"
            "- Ensure the IMAP is turned on in Yandex account settings.\n"
        )
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if mail:
            try:
                mail.close()
            except Exception:
                pass
            try:
                mail.logout()
            except Exception:
                pass


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

    for entry in sorted(os.listdir(download_dir)):
        folder_path = os.path.join(download_dir, entry)
        if not os.path.isdir(folder_path):
            continue

        meta_path = os.path.join(folder_path, "email_meta.json")
        body_path = os.path.join(folder_path, "email_body.txt")
        if not os.path.exists(meta_path):
            continue

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        body = ""
        if os.path.exists(body_path):
            with open(body_path, "r", encoding="utf-8") as f:
                body = f.read()

        # Template formatting
        subject = meta.get("subject", "") or ""
        subject_line = f' "{subject}" ' if subject else ' "(no subject)" '
        reply_text = template.format(
            sender_name=_extract_sender_name(meta.get("from", "")),
            subject_line=subject_line,
            date=meta.get("date", "unknown date"),
            body_excerpt=body[:body_excerpt_chars].strip() or "(empty body)",
            rfq_link=RFQ_DRAFT_LINK,
        )

        reply_path = os.path.join(folder_path, "reply.txt")
        with open(reply_path, "w", encoding="utf-8") as f:
            f.write(reply_text)

        print(f"  ✓ reply generated for: {entry}")
        generated += 1

    print(f"\nTotal replies generated: {generated}")
    return generated


def _extract_email_address(field: str) -> str:
    m = re.search(r"<([^>]+)>", field or "")
    return m.group(1) if m else (field or "").strip()


def send_replies(
    smtp_server: str,
    smtp_port: int,
    sender_email: str = None,
    sender_password: str = None,
    download_dir: str = DOWNLOADS_DIR,
    subfolder: str = None,
    dry_run: bool = False,
) -> int:
    """Send replies via SMTP.

    If `subfolder` is specified, only the reply for that specific email folder
    will be sent. Otherwise, it iterates through all subfolders in `download_dir`.
    """
    if not sender_email or not sender_password:
        print("sender_email and sender_password are required.")
        return 0

    sent = 0

    # Determine which folders to process based on the `subfolder` argument
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
            if os.path.isdir(os.path.join(download_dir, entry))
        ]

    for folder_path in folders_to_process:
        meta_path = os.path.join(folder_path, "email_meta.json")
        reply_path = os.path.join(folder_path, "reply.txt")

        if not (os.path.isfile(meta_path) and os.path.isfile(reply_path)):
            if subfolder:
                print(f"  ✗ Missing email_meta.json or reply.txt in {subfolder}")
            continue

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        with open(reply_path, "r", encoding="utf-8") as f:
            reply_text = f.read()

        recipient = _extract_email_address(meta.get("from", ""))
        if not recipient:
            print(
                f"  ✗ no recipient found in {os.path.basename(folder_path)}, skipping"
            )
            continue

        # Construct the email message
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = f"Re: {meta.get('subject', '')}"

        # Threading headers
        if meta.get("message_id"):
            msg["In-Reply-To"] = meta["message_id"]
            msg["References"] = meta["message_id"]

        msg.attach(MIMEText(reply_text, "plain", "utf-8"))

        if dry_run:
            print(
                f"  [dry-run] would send to {recipient} (folder: {os.path.basename(folder_path)})"
            )
            sent += 1
            continue

        # Send via SMTP
        try:
            print(f"Connecting to {smtp_server}...")
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as srv:
                print("Logging in...")
                srv.login(sender_email, sender_password)
                srv.send_message(msg)
            print(f"  ✓ sent to {recipient} (folder: {os.path.basename(folder_path)})")
            sent += 1
        except Exception as e:
            print(f"  ✗ failed for {recipient}: {e}")

    print(f"\nTotal replies sent: {sent}")
    return sent
