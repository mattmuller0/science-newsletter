---
name: brevo-send
description: Deliver the composed HTML email via the Brevo transactional email API; retry once on failure; save HTML fallback to output/ if both attempts fail
type: rigid
tools: [Bash, Write]
---

# Skill: Send Email

## Overview
This skill is **rigid** — follow the steps exactly. All credential handling goes through environment variables; never hardcode secrets.

**Inputs required in context before starting:**
- `subject` — email subject string (from `compose-email`)
- `html_body` — complete HTML string (from `compose-email`)
- `recipient_email` — string or list of strings from `config/users/<user>.json`

**Script template:** `skills/brevo-send/send.py` — copy this file to `/tmp/send_briefing.py`, then substitute the three placeholders before executing.

**Output:** Confirmation of sent Message ID, or error with fallback path.

---

## Checklist
Create these todos before starting:
- [ ] Pre-flight: verify .env exists and BREVO_API_KEY and BREVO_SENDER_EMAIL are non-empty
- [ ] Write populated script to /tmp/send_briefing.py
- [ ] Execute script
- [ ] Confirm delivery or report error

---

## Step 1 — Pre-flight check

Credentials can come from a local `.env` file (CLI use) or from environment variables already set in the shell (claude.ai/code bash environment). Check whichever is present:

```bash
# Source .env if it exists; otherwise rely on variables already in the environment
[ -f .env ] && source .env

# Verify the required variables are now set
for var in BREVO_API_KEY BREVO_SENDER_EMAIL; do
  [ -n "${!var}" ] || { echo "ERROR: $var is not set. Add it to .env or the bash environment."; exit 1; }
done
```

If any variable is missing, stop and report which ones. Do not attempt to send.

---

## Step 2 — Write the populated script

Read `skills/send-email/send.py`. Replace the three placeholders with actual values from context:

| Placeholder | Replace with |
|-------------|-------------|
| `"RECIPIENTS_PLACEHOLDER"` | A Python string `"addr@example.com"` for one recipient, or a Python list `["a@example.com", "b@example.com"]` for multiple |
| `"SUBJECT_PLACEHOLDER"` | `"""<subject string from compose-email>"""` |
| `"HTML_BODY_PLACEHOLDER"` | `"""<html_body string from compose-email>"""` |

Write the result to `/tmp/send_briefing.py`.

All recipients are delivered via **Bcc** — the `To` field shows only the sender, so recipients cannot see each other's addresses.

**Example — top of populated script (single recipient):**
```python
RECIPIENTS = "user@example.com"
SUBJECT    = """Weekly Science Briefing — May 6, 2026 (13 papers)"""
HTML_BODY  = """<!DOCTYPE html>
<html lang="en">
...full HTML here...
</html>"""
```

**Example — top of populated script (multiple recipients):**
```python
RECIPIENTS = ["user1@example.com", "user2@example.com"]
SUBJECT    = """Weekly Science Briefing — May 6, 2026 (13 papers)"""
HTML_BODY  = """<!DOCTYPE html>
<html lang="en">
...full HTML here...
</html>"""
```

Escape any literal triple-quotes inside HTML_BODY as `\"\"\"`.

---

## Step 3 — Execute

Source `.env` and run the script in a single shell invocation:

```bash
set -a && source .env && set +a && python /tmp/send_briefing.py
```

**Important:** Always source `.env` in the same shell invocation as `python`. A separate `source` call in a prior Bash tool call does not persist environment variables.

---

## Step 4 — Verify and report

**Successful output:**
```
Sent. Message ID: <202405061234.abcd1234@smtp-relay.brevo.com>
```
Report this Message ID to the user as confirmation of delivery.

**Retry output (attempt 1 fails, attempt 2 succeeds):**
```
Attempt 1 failed (HTTP 500), retrying...
Sent. Message ID: <202405061234.abcd1234@smtp-relay.brevo.com>
```

**Failure output (both attempts fail):**
```
Attempt 1 failed (HTTP 401), retrying...
Send failed after 2 attempts (HTTP 401): {"code": "unauthorized", ...}
HTML saved to output/failed-2026-05-06.html
```

Common failure causes:
- `HTTP 401 / unauthorized` → API key invalid or missing; check `BREVO_API_KEY` in `.env`
- `HTTP 403` → sender email not verified in Brevo; go to Senders & IP → Senders and confirm the address
- `HTTP 429` → rate limit; wait a few minutes and retry manually
