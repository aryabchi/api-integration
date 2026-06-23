from config import get_settings

from mail.utils import fetch_mail

if __name__ == "__main__":
    # get settings
    settings = get_settings()

    # get email attachments
    fetch_mail(
        imap_server=settings.IMAP_SERVER,
        imap_port=settings.IMAP_PORT,
        mailbox=settings.MAILBOX_NAME,
        password=settings.MAILBOX_APP_PASSWORD,
    )
