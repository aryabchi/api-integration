import os
import sys

# Path to the 'src' directory relative to this script
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config import get_settings
from mail.fetch import fetch_mail
from mail.compose import generate_replies
from mail.send import send_replies
from sevenrights.rfq.create import create_rfqs

# === Test me ===
TEST_MESSAGE_ID_FOR_REPLY = "26671782368771@mail.yandex.ru"


def main() -> None:
    # 0. get settings
    settings = get_settings()
    mailbox = settings.MAILBOX_NAME
    password = settings.MAILBOX_APP_PASSWORD

    # 1. get emails and save attachments
    # fetch_mail(
    #     imap_server=settings.IMAP_SERVER,
    #     imap_port=settings.IMAP_PORT,
    #     mailbox=mailbox,
    #     password=password,
    # )

    # 2. create RFQs
    create_rfqs(
        dry_run=False,
        test_run=True,
        subfolder=TEST_MESSAGE_ID_FOR_REPLY,
        timeout=settings.SEVEN_RIGHTS_API_AWAIT_TIMEOUT,
    )

    # 3. generate replies
    # generate_replies()

    # 4. send replies
    # set subfolder name (mail title) to send reply to specific email
    # set dry_run=True to skip real work
    # send_replies(
    #     smtp_server=settings.SMTP_SERVER,
    #     smtp_port=settings.SMTP_PORT,
    #     sender_email=mailbox,
    #     sender_password=password,
    #     subfolder=TEST_MESSAGE_ID_FOR_REPLY,
    #     dry_run=False,
    # )


if __name__ == "__main__":
    main()
