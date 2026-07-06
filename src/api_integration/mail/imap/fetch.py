import os
import json
import imaplib
import email
import traceback
import logging
from email.header import decode_header
from email.utils import parseaddr
from api_integration.mail.sanitizers import sanitize_filename
from api_integration.mail.utils import is_trusted_email
from api_integration.constants import (
    DOWNLOADS_DIR,
    IMAP_MAIL_SEARCH_TEMPLATE,
)
from api_integration.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def decode_mime_filename(filename_header):
    """Decodes MIME encoded-word syntax in filenames."""

    if not filename_header:
        return None
    decoded_fragments = decode_header(filename_header)
    decoded_filename = ""

    for fragment, charset in decoded_fragments:
        if isinstance(fragment, bytes):
            decoded_filename += fragment.decode(charset or "utf-8", errors="ignore")
        else:
            decoded_filename += fragment

    return decoded_filename


def fetch_mail(
    mailbox: str = settings.MAILBOX_NAME,
    password: str = settings.MAILBOX_APP_PASSWORD,
    mail_search_template: str = IMAP_MAIL_SEARCH_TEMPLATE,
    download_dir: str = DOWNLOADS_DIR,
    disallowed_attachment_extensions: tuple = (".json",),
    junk_subdir: str = "junk",
) -> None:
    """Connects to mailbox, searches for relevant emails and saves their
    content/attachments into per-email subfolders named by Message-ID.
    Skips processing entirely if the Message-ID folder already exists.
    """
    imap_server = settings.IMAP_SERVER
    imap_port = settings.IMAP_PORT

    os.makedirs(download_dir, exist_ok=True)
    mail = None
    try:
        logger.info(f"Connecting to {imap_server}...")
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)

        logger.info("Logging in...")
        mail.login(mailbox, password)
        mail.select("INBOX")

        # Determine search criteria based on template
        if mail_search_template.strip():
            logger.info(f"Searching for emails by pattern: '{mail_search_template}'...")
            status, messages = mail.search(None, mail_search_template)
        else:
            logger.info("Fetching all emails (no search filter)...")
            status, messages = mail.search(None, "ALL")

        if status != "OK":
            logger.warning("No emails found or search failed.")
            return

        email_ids = messages[0].split()
        logger.info(f"Found {len(email_ids)} matching email(s).")

        attachments_saved = 0
        emails_skipped = 0

        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")

            for response_part in msg_data:
                if not isinstance(response_part, tuple):
                    continue

                msg = email.message_from_bytes(response_part[1])

                # --- 1. Determine folder name based on Message-ID ---
                message_id_raw = msg.get("Message-ID", "")
                if message_id_raw:
                    # Strip angle brackets and sanitize for filesystem
                    folder_name = sanitize_filename(message_id_raw.strip().strip("<>"))
                else:
                    # Fallback if Message-ID is missing
                    folder_name = f"no_msgid_{e_id.decode()}"

                if not folder_name:
                    folder_name = f"empty_msgid_{e_id.decode()}"

                # --- 1b. Check if sender is trusted ---
                sender_email = parseaddr(msg.get("From", ""))[1]
                if not is_trusted_email(sender_email):
                    email_folder_path = os.path.join(
                        download_dir, junk_subdir, folder_name
                    )
                else:
                    email_folder_path = os.path.join(download_dir, folder_name)

                # --- 2. Skip if folder already exists ---
                if os.path.isdir(email_folder_path):
                    logger.info(f"  -> Skipping (folder already exists): {folder_name}")
                    emails_skipped += 1
                    continue

                # Create the folder since it doesn't exist
                os.makedirs(email_folder_path, exist_ok=True)

                # --- Decode subject for logging/metadata ---
                subject_raw, charset = decode_header(msg["Subject"] or "(no subject)")[
                    0
                ]
                if isinstance(subject_raw, bytes):
                    subject = subject_raw.decode(charset or "utf-8", errors="ignore")
                else:
                    subject = subject_raw or "(no subject)"

                logger.info(f"Processing email: {subject}")
                logger.info(f"  -> Saved to folder: {folder_name}")

                # --- Persist metadata ---
                metadata = {
                    "email_id": e_id.decode(),
                    "subject": subject,
                    "from": msg.get("From", ""),
                    "to": msg.get("To", ""),
                    "message_id": message_id_raw,
                    "date": msg.get("Date", ""),
                    "folder": folder_name,
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
                    if (
                        disallowed_attachment_extensions is not None
                        and ext.lower() in disallowed_attachment_extensions
                    ):
                        continue  # skip off-topic attachment

                    filepath = os.path.join(email_folder_path, filename)

                    # Handle duplicate filenames *within the same email*
                    counter = 1
                    while os.path.exists(filepath):
                        filepath = f"{base}_{counter}{ext}"
                        counter += 1

                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))

                    logger.info(
                        f"    -> Saved attachment: {os.path.basename(filepath)}"
                    )
                    attachments_saved += 1

        logger.info(f"Total attachments saved: {attachments_saved}")
        logger.info(f"Total emails skipped (already processed): {emails_skipped}")

    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP Error: {e}")
        logger.info(
            "Hints:\n"
            "- Ensure you are using an App Password, not regular Yandex password.\n"
            "- Ensure the IMAP is turned on in Yandex account settings.\n"
        )
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        traceback.print_exc()
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
