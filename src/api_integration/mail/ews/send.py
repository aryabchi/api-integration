import os
import json
import datetime
import logging
import traceback
from typing import Optional

from exchangelib import Credentials, Account, Configuration, DELEGATE, Message, Mailbox
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from exchangelib.errors import (
    UnauthorizedError,
    ErrorNonExistentMailbox,
    ErrorImpersonateUserDenied,
    ErrorMailboxStoreUnavailable,
    ErrorAccessDenied,
    ErrorInternalServerError,
    ErrorServerBusy,
    TransportError,
    ErrorInvalidIdMalformed,
    ErrorMimeContentConversionFailed,
    ErrorInvalidPropertyRequest,
    ErrorItemNotFound,
)

from api_integration.constants import (
    DOWNLOADS_DIR,
    REPLY_SENT_MARKER,
    REPLY_BODY_MARKER,
)
from api_integration.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _extract_email_address(field: str) -> str:
    import re

    m = re.search(r"<([^>]+)>", field or "")
    return m.group(1) if m else (field or "").strip()


def _is_html(text: str) -> bool:
    import re

    return bool(re.search(r"<[a-z][a-z0-9]*\b[^>]*>", text, re.IGNORECASE))


def send_replies(
    sender_email: str = settings.PRIMARY_SMTP_ADDRESS,
    sender_password: str = settings.EXCHANGE_PASSWORD,
    download_dir: str = DOWNLOADS_DIR,
    exclude: tuple = ("junk",),
    subfolder: str | None = None,
    dry_run: bool = False,
    test_run: bool = False,
) -> int:
    """Send replies via Exchange EWS.

    If `subfolder` is specified, only the reply for that specific email folder
    will be sent. Otherwise, it iterates through all subfolders in `download_dir`.

    Skips sending if the reply marker file already exists in the subfolder.
    Upon successful send, creates the marker file to prevent duplicate sends.
    """

    account = None
    try:
        logger.info("Connecting to Exchange server for sending replies...")
        credentials = Credentials(
            username=settings.EXCHANGE_USERNAME, password=sender_password
        )

        # Подменяем стандартный класс сессии в exchangelib на игнорирующий TLS validation errors
        BaseProtocol.HTTP_ADAPTER_CLS.session_class = NoVerifyHTTPAdapter
        BaseProtocol.HTTP_ADAPTER_CLS.DEFAULT_TIMEOUT = 30

        config = Configuration(server=settings.EXCHANGE_SERVER, credentials=credentials)

        account = Account(
            primary_smtp_address=sender_email,
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )
        logger.info("Configuration initialized. Checking real network connection...")
        # РЕАЛЬНЫЙ ТЕСТ: Запрашиваем версию сервера по сети.
        # Это принудительно инициирует веб-сессию и проверит credentials
        server_version = account.protocol.version

        logger.info(
            f"Successfully connected to Exchange Server! "
            f"Server version: {server_version.build}. "
            f"Access to mailbox {sender_email} succeeds."
        )
    except UnauthorizedError as e:
        logger.error(
            f"Exchange Authentication Failed: Invalid username or password. {e}"
        )
        return 0
    except ErrorNonExistentMailbox as e:
        logger.error(f"Exchange Mailbox Not Found: {sender_email}. {e}")
        return 0
    except ErrorImpersonateUserDenied as e:
        logger.error(f"Exchange Impersonation Denied: {e}")
        return 0
    except ErrorMailboxStoreUnavailable as e:
        logger.error(f"Exchange Mailbox Store Unavailable: {e}")
        return 0
    except ErrorAccessDenied as e:
        logger.error(f"Exchange Access Denied: {e}")
        return 0
    except ErrorInternalServerError as e:
        logger.error(f"Exchange Internal Server Error: {e}")
        return 0
    except ErrorServerBusy as e:
        logger.error(f"Exchange Server Busy: {e}")
        return 0
    except (ErrorInternalServerError, TransportError) as e:
        logger.error(f"Exchange Internal Server Error or Transport Error: {e}")
        return 0
    except Exception as e:
        logger.error(f"Failed to connect to Exchange: {e}")
        return 0

    if not sender_email or not sender_password:
        logger.warning("sender_email and sender_password are required.")
        return 0

    sent = 0
    skipped = 0

    try:
        # Determine which folders to process based on the `subfolder` argument
        if subfolder:
            folder_path = os.path.join(download_dir, subfolder)
            if not os.path.isdir(folder_path):
                logger.warning(f"✗ Subfolder not found: {folder_path}")
                return 0
            folders_to_process = [folder_path]
        else:
            if not os.path.isdir(download_dir):
                logger.warning(f"Download directory not found: {download_dir}")
                return 0
            folders_to_process = [
                os.path.join(download_dir, entry)
                for entry in sorted(os.listdir(download_dir))
                if os.path.isdir(os.path.join(download_dir, entry))
                and entry not in exclude
            ]

        for folder_path in folders_to_process:
            meta_path = os.path.join(folder_path, "email_meta.json")
            reply_path = os.path.join(folder_path, REPLY_BODY_MARKER)
            sent_marker_path = os.path.join(folder_path, REPLY_SENT_MARKER)

            if not (os.path.isfile(meta_path) and os.path.isfile(reply_path)):
                if subfolder:
                    logger.warning(
                        f"  ✗ Missing email_meta.json or reply.txt in {subfolder}"
                    )
                continue

            # --- Skip if reply was already sent (unless test_run mode) ---
            if os.path.exists(sent_marker_path) and not test_run:
                logger.info(
                    f"  -> Skipping (reply already sent): {os.path.basename(folder_path)}"
                )
                skipped += 1
                continue

            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                with open(reply_path, "r", encoding="utf-8") as f:
                    reply_text = f.read()

                recipient = _extract_email_address(meta.get("from", ""))
                if not recipient:
                    logger.warning(
                        f"  ✗ no recipient found in {os.path.basename(folder_path)}, skipping"
                    )
                    continue

                # Construct the email message via EWS
                subject = f"Re: {meta.get('subject', '')}"
                body = reply_text

                if dry_run:
                    logger.info(
                        f"  [dry-run] would send to {recipient} (folder: {os.path.basename(folder_path)})"
                    )
                    sent += 1
                    continue

                try:
                    msg = Message(
                        account=account,
                        folder=account.sent,
                        subject=subject,
                        body=body,
                        from_mailbox=Mailbox(email_address=sender_email),
                        to_recipients=[Mailbox(email_address=recipient)],
                    )

                    # Set threading headers if available
                    if meta.get("message_id"):
                        msg.in_reply_to = meta["message_id"]
                        msg.references = meta["message_id"]

                    # Set body type based on content
                    if _is_html(reply_text):
                        msg.body = body
                        msg.text_body = None
                    else:
                        msg.text_body = body
                        msg.body = None

                    msg.send()
                    logger.info(
                        f"  ✓ sent to {recipient} (folder: {os.path.basename(folder_path)})"
                    )
                    sent += 1

                except ErrorAccessDenied as e:
                    logger.error(
                        f"  ✗ Access denied for {recipient}: {e}. "
                        f"Check 'Send As'/'Send on Behalf' permissions for {sender_email}"
                    )
                except Exception as e:
                    logger.error(f"  ✗ failed to send to {recipient}: {e}")
                    logger.debug(traceback.format_exc())

                # --- Save placeholder file upon successful send ---
                if sent > 0:
                    try:
                        with open(sent_marker_path, "w", encoding="utf-8") as f:
                            f.write(
                                f"Reply sent on {datetime.datetime.now().isoformat()}\n"
                            )
                    except Exception as e:
                        logger.error(
                            f"Failed to write sent marker for {folder_path}: {e}"
                        )

            except Exception as e:
                logger.error(
                    f"  ✗ failed for folder {os.path.basename(folder_path)}: {e}"
                )
                logger.debug(traceback.format_exc())
                continue

    except Exception as e:
        logger.error(f"An unexpected error occurred while sending replies: {e}")
        logger.debug(traceback.format_exc())

    logger.info(f"Total replies sent: {sent}")
    logger.info(f"Total replies skipped (already sent): {skipped}")
    return sent
