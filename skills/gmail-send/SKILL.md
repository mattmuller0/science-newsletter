---
name: gmail-send
description: Send the composed HTML briefing email through the Gmail MCP send_message tool
type: rigid
tools: [ToolSearch]
---

# Skill: Send via Gmail

## Overview
This skill is **rigid** — follow the steps exactly. No credentials or environment variables needed; the Gmail MCP handles authentication. The email is **sent**, not saved as a draft.

**Inputs required in context before starting:**
- `subject` — email subject string (from `compose-email`)
- `html_body` — complete HTML string (from `compose-email`)
- `recipient_email` — string or list of strings from `config/users/<user>.json`

**Output:** Confirmation with the sent Gmail message ID.

---

## Checklist
Create these todos before starting:
- [ ] Resolve the Gmail send tool name
- [ ] Normalize recipients to a list of plain email address strings
- [ ] Send the message
- [ ] Confirm message ID and report

---

## Step 0 — Resolve the Gmail send tool

The Gmail server's prefix differs between environments (for example `mcp__Gmail__` or `mcp__claude_ai_Gmail__`). Use one `ToolSearch` call:

```
ToolSearch query: "gmail send_message create_draft"   max_results: 5
```

Record `SEND_TOOL` (the name ending in `__send_message`) and `DRAFT_TOOL` (the name ending in `__create_draft`, used only as the fallback in Step 3).

---

## Step 1 — Normalize recipients

`recipient_email` from config may be a single string or a list. Convert it to a list of plain email address strings (no display names).

**Examples:**
- `"user@example.com"` → `["user@example.com"]`
- `["user@example.com", "other@example.com"]` → `["user@example.com", "other@example.com"]`

---

## Step 2 — Send

Call `SEND_TOOL` exactly once with:

| Parameter  | Value                                      |
|------------|--------------------------------------------|
| `to`       | recipient list from Step 1                 |
| `subject`  | subject string from `compose-email`        |
| `htmlBody` | html_body string from `compose-email`      |

Do not pass `draftId`. This is a scheduled, user-configured send to the user's own address(es) in config; no further confirmation is needed.

---

## Step 3 — Confirm and report

The tool returns a message object with an `id`. Report:

```
Briefing sent to <recipients>. Gmail message ID: <id>
```

**If the send call returns an error, do not call it again.** A failed-looking call can still have delivered, and a retry risks a duplicate email. Instead, create a draft once with `DRAFT_TOOL` using the same `to`, `subject` and `htmlBody`, and report:

```
Send failed: <full error message>
Saved as a Gmail draft instead (draft ID: <id>). Open it in Gmail to send.
```

If `SEND_TOOL` is not available at all, go straight to the draft fallback and say so in the report.
