from config import get_settings

from mail.mail import (
    fetch_mail,
    generate_replies,
    send_replies,
)

# TODO: change me
EMAIL_TITLE_FOR_REPLY = r"excel с яндекс-почты"

if __name__ == "__main__":
    # get settings
    settings = get_settings()

    # 1. get emails and save attachments
    fetch_mail(
        imap_server=settings.IMAP_SERVER,
        imap_port=settings.IMAP_PORT,
        mailbox=settings.MAILBOX_NAME,
        password=settings.MAILBOX_APP_PASSWORD,
    )

    # 2. generate replies
    generate_replies()

    # 3. send replies
    # set subfolder name (mail title) to send reply to specific email
    # set dry_run=True to skip real work
    send_replies(
        smtp_server=settings.SMTP_SERVER,
        smtp_port=settings.SMTP_PORT,
        sender_email=settings.MAILBOX_NAME,
        sender_password=settings.MAILBOX_APP_PASSWORD,
        subfolder=EMAIL_TITLE_FOR_REPLY,
        dry_run=False,
    )
