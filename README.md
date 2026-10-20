# InternshipEmailSender

A small Python project that reads the sender, recipient list, subject, body, and attachments from files and sends a **separate email to each recipient** using Gmail SMTP.

## Project structure

```text
InternshipEmailSender/
├── main.py
├── sender.txt
├── recipients.txt
├── email_content.txt
├── .env                 # create this from .env.example
├── .env.example
├── .gitignore
├── requirements.txt
└── attachments/         # every regular file in this folder is attached
```

## Requirements

- Python 3.10 or newer
- A Gmail account with 2-Step Verification enabled
- A Google App Password

## Gmail setup

1. Enable 2-Step Verification for the sender Gmail account.
2. Open your Google Account security settings and create an **App Password** (if the account is eligible).
3. Copy `.env.example` to a new file named `.env`.
4. Set `GMAIL_ADDRESS` to the same address as `sender.txt`.
5. Set `GMAIL_APP_PASSWORD` to the Google App Password. Remove spaces if you prefer; the script removes spaces automatically.
6. Do not share `.env` or commit it to Git.

A normal Google account password will not work here. Google Workspace policies or Advanced Protection may prevent App Passwords from being available.

## Configure the email

### `sender.txt`

One sender email address.

### `recipients.txt`

Put one recipient per line. Comma-separated addresses are also accepted. Duplicate addresses are removed. Each recipient gets a separate message and is the only address in that message's `To` field.

### `email_content.txt`

The first line must begin with `Subject:`. Everything after the first line is the email body.

Example:

```text
Subject: Application for Software Engineering Internship

Dear Hiring Team,

Please find my resume attached.

Best regards,
David Almeida
```

### Attachments

Place all files you want attached directly inside `attachments/`. Every regular file in that folder is attached to each email. Subfolders are ignored. Remove files you do not want to send.

## Install and run on Windows PowerShell

Open PowerShell in this folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python main.py
```

If PowerShell blocks activation, you can skip activation and run:

```powershell
py -m pip install -r requirements.txt
py main.py
```

Fill in `.env` before running. The script starts sending immediately when `main.py` runs. Test first with an address you control and a harmless test message.

## Safety and behavior

- The script sends one SMTP message per recipient. It never places the whole recipient list into a single email.
- It prints success/failure for each recipient.
- It pauses one second between recipients.
- If an individual send fails, it reports the failure and continues where the SMTP connection remains usable.
- If login or the SMTP connection fails, it stops and reports the error.
- Sending can be subject to Gmail sending limits and anti-abuse protections.
- Review the recipient list and message before running; delivery begins immediately.
