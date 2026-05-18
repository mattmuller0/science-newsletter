"""
Brevo transactional email sender — stdlib only (no third-party dependencies).

Credentials are read from environment variables (sourced from .env if present,
or set directly in the shell environment). RECIPIENTS, SUBJECT, and HTML_BODY
are injected as literals by the brevo-send skill before writing this file to /tmp/.
"""

import os
import json
import urllib.request
import urllib.error
import datetime
import pathlib

# ── Credentials from environment ─────────────────────────────────────────────
required = ["BREVO_API_KEY", "BREVO_SENDER_EMAIL"]
missing = [k for k in required if not os.environ.get(k)]
if missing:
    raise SystemExit(f"Missing environment variables: {', '.join(missing)}")

API_KEY = os.environ["BREVO_API_KEY"]
SENDER  = os.environ["BREVO_SENDER_EMAIL"]

# ── Injected by skill before writing to /tmp/ ─────────────────────────────────
# RECIPIENTS: string or list of strings — all delivered via BCC
RECIPIENTS = "RECIPIENTS_PLACEHOLDER"
SUBJECT    = "SUBJECT_PLACEHOLDER"
HTML_BODY  = "HTML_BODY_PLACEHOLDER"

# Normalize to list
if isinstance(RECIPIENTS, str):
    RECIPIENTS = [RECIPIENTS]


# ── Brevo API send ────────────────────────────────────────────────────────────
def send():
    payload = json.dumps({
        "sender":      {"email": SENDER},
        "to":          [{"email": SENDER}],          # sender visible in To; recipients hidden
        "bcc":         [{"email": r} for r in RECIPIENTS],
        "subject":     SUBJECT,
        "htmlContent": HTML_BODY,
    }).encode()
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=payload,
        headers={
            "api-key":      API_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    print(f"Sent. Message ID: {result['messageId']}")


# ── Main: send with one retry ─────────────────────────────────────────────────
for attempt in (1, 2):
    try:
        send()
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
