from config import get_settings

from mail.fetch import fetch_mail
from mail.compose import generate_replies
from mail.send import send_replies

# TODO: test me
TEST_MESSAGE_ID_FOR_REPLY = None  # r"87311782287117@mail.yandex.ru"


def main() -> None:
    # get settings
    settings = get_settings()
    mailbox = settings.MAILBOX_NAME
    password = settings.MAILBOX_APP_PASSWORD

    # 1. get emails and save attachments
    fetch_mail(
        imap_server=settings.IMAP_SERVER,
        imap_port=settings.IMAP_PORT,
        mailbox=mailbox,
        password=password,
    )

    # 2. generate replies
    generate_replies()

    # 3. send replies
    # set subfolder name (mail title) to send reply to specific email
    # set dry_run=True to skip real work
    send_replies(
        smtp_server=settings.SMTP_SERVER,
        smtp_port=settings.SMTP_PORT,
        sender_email=mailbox,
        sender_password=password,
        subfolder=TEST_MESSAGE_ID_FOR_REPLY,
        dry_run=False,
    )


if __name__ == "__main__":
    main()
