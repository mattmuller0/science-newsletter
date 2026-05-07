"""
Gmail REST API sender — stdlib only (no third-party dependencies).

Credentials are read from environment variables (sourced from .env if present,
or set directly in the shell environment). RECIPIENTS, SUBJECT, and HTML_BODY
are injected as literals by the send-email skill before writing this file to /tmp/.
"""

import os
import base64
import json
import urllib.request
import urllib.parse
import urllib.error
import datetime
import pathlib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── Credentials from environment ─────────────────────────────────────────────
required = ["GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN", "GMAIL_SENDER_EMAIL"]
missing = [k for k in required if not os.environ.get(k)]
if missing:
    raise SystemExit(f"Missing environment variables: {', '.join(missing)}")

CLIENT_ID     = os.environ["GMAIL_CLIENT_ID"]
CLIENT_SECRET = os.environ["GMAIL_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["GMAIL_REFRESH_TOKEN"]
SENDER        = os.environ["GMAIL_SENDER_EMAIL"]

# ── Injected by skill before writing to /tmp/ ─────────────────────────────────
# RECIPIENTS: string or list of strings — all delivered via BCC
RECIPIENTS = "RECIPIENTS_PLACEHOLDER"
SUBJECT    = "SUBJECT_PLACEHOLDER"
HTML_BODY  = "HTML_BODY_PLACEHOLDER"

# Normalize to list
if isinstance(RECIPIENTS, str):
    RECIPIENTS = [RECIPIENTS]


# ── Token exchange ────────────────────────────────────────────────────────────
def get_access_token():
    data = urllib.parse.urlencode({
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type":    "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


# ── MIME construction ─────────────────────────────────────────────────────────
def build_raw_message():
    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"]    = SENDER
    msg["To"]      = SENDER                          # sender visible in To; recipients hidden
    msg["Bcc"]     = ", ".join(RECIPIENTS)           # Gmail strips Bcc before delivery
    msg.attach(MIMEText(HTML_BODY, "html"))
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


# ── Gmail API send ────────────────────────────────────────────────────────────
def send(access_token, raw_message):
    payload = json.dumps({"raw": raw_message}).encode()
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    print(f"Sent. Message ID: {result['id']}")


# ── Main: send with one retry ─────────────────────────────────────────────────
raw = build_raw_message()
for attempt in (1, 2):
    try:
        token = get_access_token()
        send(token, raw)
        break
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if attempt == 2:
            today = datetime.date.today().isoformat()
            out   = pathlib.Path(f"output/failed-{today}.html")
            out.parent.mkdir(exist_ok=True)
            out.write_text(HTML_BODY)
            raise SystemExit(
                f"Send failed after 2 attempts (HTTP {e.code}): {body}\n"
                f"HTML saved to {out}"
            )
        print(f"Attempt {attempt} failed (HTTP {e.code}), retrying...")
