"""Helper Functions"""

import os
import imaplib
import email
from email.header import decode_header
from mail.sanitizers import sanitize_filename
from constants import (
    DOWNLOADS_DIR,
    ALLOWED_ATTACHMENT_FILE_EXTENSIONS,
    IMAP_MAIL_SEARCH_TEMPLATE,
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


def fetch_mail(
    imap_server: str,
    imap_port: int,
    mailbox: str,
    password: str,
    imap_mail_search_template: str = IMAP_MAIL_SEARCH_TEMPLATE,
    download_dir: str = DOWNLOADS_DIR,
    allowed_attachemnt_extensions: tuple = ALLOWED_ATTACHMENT_FILE_EXTENSIONS,
) -> None:
    """Connects to mailbox, searches for relevant emails and saves their attachments"""
    # Create download directory if it doesn't exist
    os.makedirs(download_dir, exist_ok=True)

    mail = None
    try:
        print(f"Connecting to {imap_server}...")
        # Connect to Yandex IMAP server over SSL
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)

        print("Logging in...")
        mail.login(mailbox, password)

        mail.select("INBOX")

        print(f"Searching for emails by pattern: '{imap_mail_search_template}'...")

        status, messages = mail.search(
            None,
            imap_mail_search_template,
        )

        if status != "OK":
            print("No emails found or search failed.")
            return

        email_ids = messages[0].split()
        print(f"Found {len(email_ids)} matching email(s).")

        attachments_saved = 0

        # Loop through each email ID
        for e_id in email_ids:
            # Fetch the email content (RFC822 gets the whole raw email)
            status, msg_data = mail.fetch(e_id, "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # Parse the raw bytes into an email message object
                    msg = email.message_from_bytes(response_part[1])
                    subject, charset = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(charset or "utf-8", errors="ignore")

                    print(f"\nProcessing email: {subject}")

                    # Iterate over all parts of the email
                    for part in msg.walk():
                        # Check if this part has a filename (indicating an attachment)
                        filename_raw = part.get_filename()

                        if filename_raw:
                            filename = decode_mime_filename(filename_raw)
                            filename = sanitize_filename(filename)

                            if not filename:
                                continue

                            filepath = os.path.join(download_dir, filename)

                            # Handle duplicate filenames
                            counter = 1
                            base, ext = os.path.splitext(filepath)
                            if ext not in allowed_attachemnt_extensions:
                                # skip off-topic attachment
                                continue

                            while os.path.exists(filepath):
                                filepath = f"{base}_{counter}{ext}"
                                counter += 1

                            # Save the attachment
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
        # Clean up and close the connection
        if mail:
            try:
                mail.close()
            except:
                pass
            mail.logout()
