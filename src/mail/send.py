import os
import re
import json
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from constants import (
    DOWNLOADS_DIR,
    REPLY_SENT_MARKER,
)


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

    Skips sending if the reply marker file already exists in the subfolder.
    Upon successful send, creates the marker file to prevent duplicate sends.
    """

    if not sender_email or not sender_password:
        print("sender_email and sender_password are required.")
        return 0

    sent = 0
    skipped = 0

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
        sent_marker_path = os.path.join(folder_path, REPLY_SENT_MARKER)

        if not (os.path.isfile(meta_path) and os.path.isfile(reply_path)):
            if subfolder:
                print(f"  ✗ Missing email_meta.json or reply.txt in {subfolder}")
            continue

        # --- Skip if reply was already sent ---
        if os.path.exists(sent_marker_path):
            print(
                f"  -> Skipping (reply already sent): {os.path.basename(folder_path)}"
            )
            skipped += 1
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
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as srv:
                srv.login(sender_email, sender_password)
                srv.send_message(msg)

            # --- Save placeholder file upon successful send ---
            with open(sent_marker_path, "w", encoding="utf-8") as f:
                f.write(f"Reply sent on {datetime.datetime.now().isoformat()}\n")

            print(f"  ✓ sent to {recipient} (folder: {os.path.basename(folder_path)})")
            sent += 1
        except Exception as e:
            print(f"  ✗ failed for {recipient}: {e}")

    print(f"\nTotal replies sent: {sent}")
    print(f"Total replies skipped (already sent): {skipped}")
    return sent
