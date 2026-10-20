"""
InternshipEmailSender
Sends a separate email to each recipient listed in recipients.txt.

Run:
    python main.py

Gmail setup:
1. Enable 2-Step Verification on the sender's Google account.
2. Create a Google App Password and put it in .env.
3. Never use your normal Gmail password here.
"""
from __future__ import annotations

import mimetypes
import os
import smtplib
import ssl
import sys
import time
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ATTACHMENTS_DIR = BASE_DIR / "attachments"
SENDER_FILE = BASE_DIR / "sender.txt"
RECIPIENTS_FILE = BASE_DIR / "recipients.txt"
CONTENT_FILE = BASE_DIR / "email_content.txt"
ENV_FILE = BASE_DIR / ".env"


def read_required_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path.name}")
    content = path.read_text(encoding="utf-8-sig").strip()
    if not content:
        raise ValueError(f"{path.name} is empty.")
    return content


def read_recipients(path: Path) -> list[str]:
    raw = read_required_text(path)
    # Accept one email per line, and also comma/semicolon-separated addresses.
    recipients: list[str] = []
    for line in raw.splitlines():
        for item in line.replace(";", ",").split(","):
            address = item.strip()
            if address and not address.startswith("#") and address not in recipients:
                recipients.append(address)
    if not recipients:
        raise ValueError("No recipient email addresses found in recipients.txt.")
    return recipients


def read_subject_and_body(path: Path) -> tuple[str, str]:
    content = read_required_text(path)
    lines = content.splitlines()
    if not lines or not lines[0].strip().lower().startswith("subject:"):
        raise ValueError(
            "The first line of email_content.txt must start with 'Subject:'."
        )
    subject = lines[0].split(":", 1)[1].strip()
    body = "\n".join(lines[1:]).strip()
    if not subject:
        raise ValueError("Email subject is empty.")
    if not body:
        raise ValueError("Email body is empty.")
    return subject, body


def collect_attachments(folder: Path) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    # Only attach regular files directly inside attachments/; ignore subfolders.
    return sorted(p for p in folder.iterdir() if p.is_file() and not p.name.startswith("."))


def build_message(sender: str, recipient: str, subject: str, body: str,
                  attachment_paths: list[Path]) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient  # Exactly one recipient per message.
    message["Subject"] = subject
    message.set_content(body)

    for path in attachment_paths:
        mime_type, _ = mimetypes.guess_type(path.name)
        if mime_type:
            maintype, subtype = mime_type.split("/", 1)
        else:
            maintype, subtype = "application", "octet-stream"
        with path.open("rb") as file:
            message.add_attachment(
                file.read(),
                maintype=maintype,
                subtype=subtype,
                filename=path.name,
            )
    return message


def main() -> int:
    load_dotenv(ENV_FILE)

    try:
        sender = read_required_text(SENDER_FILE).splitlines()[0].strip()
        recipients = read_recipients(RECIPIENTS_FILE)
        subject, body = read_subject_and_body(CONTENT_FILE)
        attachment_paths = collect_attachments(ATTACHMENTS_DIR)

        username = os.getenv("GMAIL_ADDRESS", "").strip()
        app_password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
        if not username or not app_password:
            raise ValueError(
                "Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in the .env file."
            )
        if sender.lower() != username.lower():
            raise ValueError(
                "The email in sender.txt must match GMAIL_ADDRESS in .env."
            )

    except (OSError, ValueError) as exc:
        print(f"Setup error: {exc}", file=sys.stderr)
        return 2

    print(f"Sender: {sender}")
    print(f"Recipients: {len(recipients)}")
    print(f"Attachments: {len(attachment_paths)}")
    if attachment_paths:
        for path in attachment_paths:
            print(f"  - {path.name}")
    print("\nStarting individual email delivery...\n")

    context = ssl.create_default_context()
    sent = 0
    failed = 0

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(username, app_password)

            for index, recipient in enumerate(recipients, start=1):
                try:
                    message = build_message(
                        sender, recipient, subject, body, attachment_paths
                    )
                    server.send_message(message)
                    sent += 1
                    print(f"[{index}/{len(recipients)}] SENT   {recipient}")
                except (smtplib.SMTPException, OSError, ValueError) as exc:
                    failed += 1
                    print(
                        f"[{index}/{len(recipients)}] FAILED {recipient}: "
                        f"{type(exc).__name__}: {exc}"
                    )

                # Brief pause between messages to avoid rapid-fire sending.
                if index < len(recipients):
                    time.sleep(1.0)

    except (smtplib.SMTPException, OSError) as exc:
        print(
            f"\nSMTP connection/login error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        print("No further emails were attempted after this connection error.")
        return 1

    print("\n--- Summary ---")
    print(f"Sent successfully: {sent}")
    print(f"Failed:            {failed}")
    print(f"Total recipients:  {len(recipients)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
