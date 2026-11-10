# Science Briefer — Orchestration Agent

## Purpose
Produce a weekly research briefing email for a single user by searching PubMed for recent papers and bioRxiv, medRxiv and arXiv for recent preprints, curating them against the user's research profile, writing technical summaries, composing an HTML email, and sending it via Gmail.

## Runtime Environment
- Working directory: project root (wherever this repo is checked out)
- Skills live in `skills/`; user profiles in `agents/users/`; search configs in `config/users/`; helper scripts in `scripts/`
- Email is sent through the Gmail MCP `send_message` tool (no credentials needed)
- Preprints are fetched by `scripts/fetch_preprints.py` (Python 3 standard library only) from the public bioRxiv/medRxiv and arXiv APIs; no connector needed. A bioRxiv MCP, if connected, is only a fallback.

## Execution Steps

### Step 1 — Load config and profile
Locate the user's files, checking in this order and using the first location that has both:
1. In the repo: `config/users/<user>.json` and `agents/users/<user>.md`
2. In `$SCIENCE_NEWSLETTER_HOME` (if set), same relative paths
3. In `~/.science-newsletter/`, same relative paths (this is where `templates/env-setup.sh` writes them)
4. In Google Drive, when a Google Drive tool is available: in the folder the run prompt names (default title `science-newsletter-config`), find the files titled `<user>.json` and `<user>.md` with `search_files` (for example `title = '<user>.json' and trashed = false`, plus `parentId = '<folder id>'` once the folder is found) and read each with `read_file_content`. Write their text verbatim to the repo paths and confirm the JSON parses before continuing.

If found outside the repo, copy both into the repo paths (they are gitignored) so every skill reads them from one place. If neither file is found anywhere, stop: do not search, compose or send anything, and report which locations were checked.

Read the user's JSON config (`config/users/<user>.json`) and their profile (`agents/users/<user>.md`). Hold both in context for all subsequent steps. The config supplies PubMed searches, preprint feeds and arXiv searches, date window, result limits, and section targets (an ordered list of sections). The profile supplies curation criteria per section and summary style.

### Step 2 — Search and fetch papers and preprints
Invoke skill: `skills/search-and-fetch/SKILL.md`

### Step 3 — Curate and summarize
Invoke skill: `skills/curate-and-summarize/SKILL.md`

### Step 4 — Compose email
Invoke skill: `skills/compose-email/SKILL.md`

### Step 5 — Send via Gmail
Invoke skill: `skills/gmail-send/SKILL.md`

## Error Handling
- A search returning 0 results: skip silently; do not reduce section targets.
- Preprint fetch failure: use the fallbacks in `search-and-fetch` Step 6; if they fail too, continue with PubMed alone and mention it in the final report. Never block the briefing on preprints.
- Fewer total candidates than needed: expand date window to 14 days and re-run searches that returned <5 results.
- Gmail send failure: do not retry the send; save a draft once instead and report the full MCP error (see `gmail-send`).

## Multi-User Notes
Each user has their own config and profile file. To run for a different user, change the `<user>` slug in Step 1. Nothing else changes.
