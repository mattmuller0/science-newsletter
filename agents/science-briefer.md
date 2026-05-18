# Science Briefer — Orchestration Agent

## Purpose
Produce a weekly research briefing email for a single user by searching PubMed for recent papers, curating them against the user's research profile, writing technical summaries, composing an HTML email, and delivering it via Gmail.

## Runtime Environment
- Working directory: project root (wherever this repo is checked out)
- Skills live in `skills/`; user profiles in `agents/users/`; search configs in `config/users/`
- Environment variables for Brevo are in `.env` (never committed)

## Execution Steps

### Step 1 — Load config and profile
Read the user's JSON config (`config/users/<user>.json`) and their profile (`agents/users/<user>.md`). Hold both in context for all subsequent steps. The config supplies search queries, date window, result limits, and section targets. The profile supplies curation criteria and summary style.

### Step 2 — Search and fetch papers
Invoke skill: `skills/search-and-fetch/SKILL.md`

### Step 3 — Curate and summarize
Invoke skill: `skills/curate-and-summarize/SKILL.md`

### Step 4 — Compose email
Invoke skill: `skills/compose-email/SKILL.md`

### Step 5 — Send email
Invoke skill: `skills/brevo-send/SKILL.md`

## Error Handling
- A search returning 0 results: skip silently; do not reduce section targets.
- Fewer total candidates than needed: expand date window to 14 days and re-run searches that returned <5 results.
- Gmail send failure: skill handles one retry; on second failure saves draft to `output/failed-<YYYY-MM-DD>.html`.
- Missing `.env` or empty OAuth variables: abort with a clear error message listing the missing variables; do not attempt to send.

## Multi-User Notes
Each user has their own config and profile file. To run for a different user, change the `<user>` slug in Step 1. Nothing else changes.
