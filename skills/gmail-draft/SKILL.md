---
name: gmail-draft
description: Create a Gmail draft of the composed HTML email using the Gmail MCP tool
type: rigid
tools: [mcp__claude_ai_Gmail__create_draft]
---

# Skill: Create Gmail Draft

## Overview
This skill is **rigid** — follow the steps exactly. No credentials or environment variables needed; the Gmail MCP handles authentication.

**Inputs required in context before starting:**
- `subject` — email subject string (from `compose-email`)
- `html_body` — complete HTML string (from `compose-email`)
- `recipient_email` — string or list of strings from `config/users/<user>.json`

**Output:** Confirmation with the Gmail draft ID.

---

## Checklist
Create these todos before starting:
- [ ] Normalize recipients to a list of plain email address strings
- [ ] Call mcp__claude_ai_Gmail__create_draft
- [ ] Confirm draft ID and report to user

---

## Step 1 — Normalize recipients

`recipient_email` from config may be a single string or a list. Convert it to a list of plain email address strings (no display names).

**Examples:**
- `"user@example.com"` → `["user@example.com"]`
- `["user@example.com", "other@example.com"]` → `["user@example.com", "other@example.com"]`

---

## Step 2 — Create the draft

Call `mcp__claude_ai_Gmail__create_draft` with:

| Parameter  | Value                                      |
|------------|--------------------------------------------|
| `to`       | recipient list from Step 1                 |
| `subject`  | subject string from `compose-email`        |
| `htmlBody` | html_body string from `compose-email`      |

---

## Step 3 — Confirm and report

The tool returns a draft ID. Report it to the user:

```
Draft created. Gmail draft ID: <id>
Open it in Gmail to review and send.
```

If the tool returns an error, report the full error message and do not retry — the draft was not created.
