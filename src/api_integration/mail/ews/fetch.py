import os
import json
import logging
import traceback
from email.header import decode_header

from exchangelib import Credentials, Account, Configuration, DELEGATE, FileAttachment
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from exchangelib.errors import (
    UnauthorizedError,
    ErrorNonExistentMailbox,
    ErrorImpersonationDenied,
    ErrorAccessDenied,
    ErrorInternalServerError,
    ErrorServerBusy,
    TransportError,
)

from api_integration.mail.sanitizers import sanitize_filename
from api_integration.mail.utils import is_trusted_email
from api_integration.constants import DOWNLOADS_DIR
from api_integration.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def fetch_mail(
    mailbox: str = settings.PRIMARY_SMTP_ADDRESS,
    password: str = settings.EXCHANGE_PASSWORD,
    mail_search_template: str = "",
    download_dir: str = DOWNLOADS_DIR,
    disallowed_attachment_extensions: tuple = (".json",),
    junk_subdir: str = "junk",
) -> None:
    """Connects to Exchange mailbox via EWS, searches for emails and saves their
    content/attachments into per-email subfolders named by Message-ID.
    Skips processing entirely if the Message-ID folder already exists.

    Args:
        mailbox: Exchange mailbox (primary SMTP address).
        password: Exchange password.
        mail_search_template: Mail search template (ignored for Exchange; kept for signature parity).
        download_dir: Local directory to save emails.
        disallowed_attachment_extensions: Tuple of lowercase extensions to skip.
        junk_subdir: Subfolder name for untrusted senders.
    """

    os.makedirs(download_dir, exist_ok=True)

    account = None
    try:
        logger.info(f"Connecting to Exchange server: {settings.EXCHANGE_SERVER}...")

        credentials = Credentials(
            username=settings.EXCHANGE_USERNAME,
            password=password,
        )

        # 2. Подменяем стандартный класс сессии в exchangelib на игнорирующий TLS validation errors
        BaseProtocol.HTTP_ADAPTER_CLS.session_class = NoVerifyHTTPAdapter
        BaseProtocol.TIMEOUT = 30

        config = Configuration(
            server=settings.EXCHANGE_SERVER,
            credentials=credentials,
        )

        account = Account(
            primary_smtp_address=mailbox,
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )
        logging.info("Configuration initialized. Checking real network connection...")
        # РЕАЛЬНЫЙ ТЕСТ: Запрашиваем версию сервера по сети.
        # Это принудительно инициирует веб-сессию и проверит ваши credentials
        server_version = account.protocol.version

        logging.info(
            f"Successfully connected to Exchange Server! "
            f"Server version: {server_version.build}. "
            f"Access to mailbox {mailbox} succeeds."
        )

        # Access inbox
        inbox = account.inbox
        logger.info("Fetching emails from inbox...")

        # Retrieve only unread messages, newest first
        messages = inbox.filter(is_read=False).order_by("-datetime_received")
        email_ids = list(messages)
        logger.info(f"Found {len(email_ids)} unread email(s) in inbox.")

        attachments_saved = 0
        emails_skipped = 0

        for message in email_ids:
            try:
                att_saved, email_skipped = _process_single_message(
                    message,
                    download_dir=download_dir,
                    disallowed_attachment_extensions=disallowed_attachment_extensions,
                    junk_subdir=junk_subdir,
                )
                attachments_saved += att_saved
                emails_skipped += email_skipped
            except Exception as e:
                logger.error(
                    f"Failed to process email Message-ID='{message.message_id}' "
                    f"Subject='{message.subject}': {e}\n{traceback.format_exc()}"
                )
                continue

        logger.info(f"Total attachments saved: {attachments_saved}")
        logger.info(f"Total emails skipped (already processed): {emails_skipped}")

    except UnauthorizedError as e:
        logger.error(
            f"Exchange Authentication Failed: Invalid username or password. {e}"
        )
    except ErrorNonExistentMailbox as e:
        # Убедитесь, что переменная mailbox определена выше в вашей функции
        logger.error(f"Exchange Mailbox Not Found: {mailbox}. {e}")

    except ErrorImpersonationDenied as e:
        logger.error(f"Exchange Impersonation Denied: {e}")

    except ErrorAccessDenied as e:
        logger.error(f"Exchange Access Denied: {e}")

    except ErrorServerBusy as e:
        logger.error(f"Exchange Server Busy: {e}")

    except (ErrorInternalServerError, TransportError) as e:
        # Объединяем внутренние ошибки сервера и недоступность базы данных/хранилища
        logger.error(
            f"Exchange Internal Server Error or Mailbox Store Unavailable: {e}"
        )

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        logger.debug(traceback.format_exc())
    finally:
        if account:
            try:
                # EWS uses persistent HTTP connections; no explicit logout needed
                logger.debug(
                    "Exchange account session cleanup (no explicit logout required)."
                )
            except Exception:
                pass


def _process_single_message(
    message,
    download_dir: str,
    disallowed_attachment_extensions: tuple,
    junk_subdir: str,
) -> tuple[int, int]:
    """Processes a single Exchange message: saves metadata, body, and attachments.
    Returns tuple of (attachments_saved, emails_skipped).
    """

    # --- 1. Determine folder name based on Message-ID ---
    message_id_raw = message.message_id or ""
    if message_id_raw:
        folder_name = sanitize_filename(message_id_raw.strip().strip("<>"))
    else:
        folder_name = f"no_msgid_{id(message)}"

    if not folder_name:
        folder_name = f"empty_msgid_{id(message)}"

    # --- 1b. Check if sender is trusted ---
    sender_email = message.sender.email_address if message.sender else ""
    if not is_trusted_email(sender_email):
        email_folder_path = os.path.join(download_dir, junk_subdir, folder_name)
    else:
        email_folder_path = os.path.join(download_dir, folder_name)

    # --- 2. Skip if folder already exists ---
    if os.path.isdir(email_folder_path):
        logger.info(f"  -> Skipping (folder already exists): {folder_name}")
        return 0, 1

    # Create the folder since it doesn't exist
    os.makedirs(email_folder_path, exist_ok=True)

    # --- Decode subject for logging/metadata ---
    subject_raw = message.subject or "(no subject)"
    try:
        decoded_fragments = decode_header(subject_raw)
        subject = ""
        for fragment, charset in decoded_fragments:
            if isinstance(fragment, bytes):
                subject += fragment.decode(charset or "utf-8", errors="ignore")
            else:
                subject += fragment
        subject = subject.strip() or "(no subject)"
    except Exception as e:
        logger.warning(f"Failed to decode subject '{subject_raw}': {e}")
        subject = subject_raw

    logger.info(f"Processing email: {subject}")
    logger.info(f"  -> Saved to folder: {folder_name}")

    # --- Persist metadata ---
    metadata = {
        "email_id": str(message.id) if message.id else "",
        "subject": subject,
        "from": message.sender.email_address if message.sender else "",
        "to": message.to_recipients[0].email_address if message.to_recipients else "",
        "message_id": message_id_raw,
        "date": (
            message.datetime_received.isoformat() if message.datetime_received else ""
        ),
        "folder": folder_name,
    }
    with open(
        os.path.join(email_folder_path, "email_meta.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # --- Extract body (prefer text/plain, fallback to text/html) ---
    body_text, body_html = "", ""
    if message.body:
        # exchangelib provides body as HTML by default; attempt to get text if available
        body_text = message.text_body or ""
        body_html = message.body or ""

    with open(
        os.path.join(email_folder_path, "email_body.txt"), "w", encoding="utf-8"
    ) as f:
        f.write(body_text or body_html)

    # --- Save attachments ---
    attachments_count = 0
    if message.attachments:
        for attachment in message.attachments:
            try:
                saved = _process_attachment(
                    attachment,
                    email_folder_path,
                    disallowed_attachment_extensions,
                )
                attachments_count += saved
            except Exception as e:
                logger.error(
                    f"Failed to save attachment '{attachment.name}' for email '{subject}': {e}"
                )
                continue

    return attachments_count, 0


def _process_attachment(
    attachment,
    email_folder_path: str,
    disallowed_attachment_extensions: tuple,
) -> int:
    """Processes a single attachment, saving it to disk if allowed.
    Returns 1 if saved successfully, 0 otherwise.
    """

    # Only handle physical file attachments
    if not isinstance(attachment, FileAttachment):
        logger.info(
            f"Skipping non-file attachment type: {type(attachment).__name__} ({getattr(attachment, 'name', 'Unknown')})"
        )
        return 0

    filename = sanitize_filename(attachment.name)
    if not filename:
        logger.warning("Attachment filename is empty after sanitization, skipping.")
        return 0

    base, ext = os.path.splitext(filename)
    if (
        disallowed_attachment_extensions is not None
        and ext.lower() in disallowed_attachment_extensions
    ):
        logger.debug(f"Skipping disallowed attachment extension: {filename}")
        return 0

    filepath = os.path.join(email_folder_path, filename)

    # Handle duplicate filenames within the same email folder
    counter = 1
    while os.path.exists(filepath):
        filepath = f"{base}_{counter}{ext}"
        counter += 1

    logger.info(f"    -> Saving attachment: {os.path.basename(filepath)}")

    # Write binary content
    try:
        with open(filepath, "wb") as f:
            f.write(attachment.content)
        return 1
    except Exception as e:
        logger.error(f"Failed to write attachment '{filename}' to disk: {e}")
        return 0
