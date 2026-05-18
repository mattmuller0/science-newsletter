# Science Newsletter

An automated weekly research briefing delivered to your inbox. Claude searches PubMed for recent papers, curates them against your research profile, writes dense technical summaries, and sends a styled HTML email — all from a single prompt or on a recurring schedule.

---

## What it produces

Each issue contains two sections configured to your interests:

**Section I — Cardiovascular Research** (or whatever domain you set)
Papers selected from high-prestige journals, prioritizing mechanistic findings and omics data. Each entry includes authors, journal, publication month, a DOI link, and a 2–3 sentence technical summary.

**Section II — Methodology Developments**
Computational methods papers, single-cell and spatial atlases, and ML/genomics tools relevant to your active toolkit.

Example entry:

> **Inhibiting Thromboinflammation via Interleukin-4 Binding to Platelet Glycoprotein VI and Suppression of Thrombosis**
> Lin S et al.  |  Blood, May 2026
>
> IL-4 directly binds platelet glycoprotein VI (GPVI) and suppresses thrombosis by dampening downstream platelet activation signaling, revealing an unexpected anti-thrombotic role for a cytokine studied primarily in allergic and Th2 immune contexts. This finding identifies GPVI as a molecular interface between inflammatory cytokine signaling and platelet function, with direct implications for understanding thromboinflammation in cardiovascular disease.

---

## How it works

1. **Search** — Up to 10 configurable PubMed queries run in parallel subagents, each scoped to a date window (default: last 7 days).
2. **Curate** — Papers are deduplicated, filtered for article type and abstract presence, then scored against your research profile.
3. **Summarize** — Selected papers get 2–3 sentence technical summaries written to your specified style and audience level.
4. **Deliver** — A styled HTML email is composed and sent via the Brevo transactional email API.

All search queries, section targets, curation criteria, and recipient addresses live in config files — nothing is hardcoded.

---

## Prerequisites

- A [Claude Code](https://claude.ai/code) account (or Claude Code CLI)
- A free [Brevo](https://www.brevo.com) account (for email sending)
- Python 3 (stdlib only — no packages needed)

---

## Setup

### 1. Clone and enter the repo

```bash
git clone <your-fork-url>
cd science-newsletter
```

### 2. Set up Brevo for email sending

1. Create a free account at [brevo.com](https://www.brevo.com).
2. Go to **Senders & IP → Senders**, click **Add a sender**, enter the email address you want to send from, and click the verification link Brevo sends to that address.
3. Go to **SMTP & API → API Keys**, click **Generate a new API key**, copy the key.

### 3. Create your `.env` file

```bash
cp .env.example .env
```

Fill in both values:

```
BREVO_API_KEY=<your API key>
BREVO_SENDER_EMAIL=<the address you verified in Brevo>
```

`.env` is gitignored and never committed.

### 4. Create your user config and profile

```bash
cp templates/user-config.json config/users/<yourname>.json
cp templates/user-profile.md  agents/users/<yourname>.md
```

Edit both files:

- **`config/users/<yourname>.json`** — set your recipient email(s), date window, result limits, and PubMed search queries.
- **`agents/users/<yourname>.md`** — describe your research focus, which journals to prioritize, and the curation criteria for each section.

Both files are gitignored and never committed.

### 5. Install the skills into Claude Code

Copy the `skills/` directory into your Claude Code skills folder:

```bash
cp -r skills/* ~/.claude/skills/
```

Or symlink it so edits to the repo are reflected immediately:

```bash
ln -s "$(pwd)/skills/search-and-fetch"    ~/.claude/skills/search-and-fetch
ln -s "$(pwd)/skills/curate-and-summarize" ~/.claude/skills/curate-and-summarize
ln -s "$(pwd)/skills/compose-email"        ~/.claude/skills/compose-email
ln -s "$(pwd)/skills/brevo-send"           ~/.claude/skills/brevo-send
```

---

## Running manually

Open Claude Code in the project root and send:

```
Run agents/science-briefer.md for user <yourname>.
```

Claude will execute all steps end-to-end and confirm the sent Message ID when done.

---

## Running as a weekly routine on claude.ai/code

Claude.ai/code supports scheduled routines that run Claude automatically on a cadence. Because `.env` files are local, you supply your credentials through the bash environment instead.

### Step 1 — Add credentials to the bash environment

In your claude.ai/code project settings, open **Bash environment** and add:

```bash
export BREVO_API_KEY="<your API key>"
export BREVO_SENDER_EMAIL="<your sender address>"
```

These are stored encrypted in your project and are not committed to the repo.

The `brevo-send` skill sources `.env` if present, and falls back to the environment automatically — no changes to the skill are needed.

### Step 2 — Create a routine

In your claude.ai/code project, create a new routine with:

- **Schedule**: weekly (e.g., every Monday at 8 AM)
- **Prompt**:

```
Run agents/science-briefer.md for user <yourname>.
```

That's it. Claude will search, curate, compose, and deliver the briefing on schedule.

---

## Customization

| What to change | Where |
|----------------|-------|
| Search queries | `config/users/<you>.json` → `searches` array |
| Date window (default 7 days) | `config/users/<you>.json` → `date_window_days` |
| Papers per section | `config/users/<you>.json` → `section_targets` |
| Curation criteria | `agents/users/<you>.md` → Section I / Section II |
| Summary style and tone | `agents/users/<you>.md` → Summary Tone and Style |
| Email template | `skills/compose-email/template.html` |
| Recipients | `config/users/<you>.json` → `recipient_email` (string or list; all delivered via BCC) |

---

## Project structure

```
.
├── agents/
│   ├── science-briefer.md        # Orchestration agent
│   └── users/                    # User profiles — gitignored
├── config/
│   └── users/                    # Per-user search configs — gitignored
├── skills/
│   ├── search-and-fetch/         # PubMed search and metadata fetch
│   ├── curate-and-summarize/     # Scoring, selection, and summarization
│   ├── compose-email/            # HTML email rendering
│   └── brevo-send/               # Brevo API delivery
├── templates/
│   ├── user-config.json          # Starter template for config/users/<name>.json
│   └── user-profile.md          # Starter template for agents/users/<name>.md
├── output/                       # Failed-send fallbacks — gitignored
├── .env                          # Credentials — gitignored
└── .env.example                  # Template for .env
```

---

## Security notes

- Credentials live in `.env` (local) or the claude.ai/code bash environment (cloud) — never in the repo.
- User configs and profiles are gitignored — your email addresses and research identity stay local.
- A pre-commit hook blocks accidental commits of email addresses or API keys.
- The Brevo API key only authorizes sending — it cannot read email or access other services.
