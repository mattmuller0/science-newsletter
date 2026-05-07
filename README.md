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
4. **Deliver** — A styled HTML email is composed and sent via the Gmail API using OAuth2.

All search queries, section targets, curation criteria, and recipient addresses live in config files — nothing is hardcoded.

---

## Prerequisites

- A [Claude Code](https://claude.ai/code) account (or Claude Code CLI)
- A Google account with Gmail that you will use as the **sender**
- A Google Cloud project (free tier is sufficient)
- Python 3 (stdlib only — no packages needed)

---

## Setup

### 1. Clone and enter the repo

```bash
git clone <your-fork-url>
cd science-newsletter
```

### 2. Create a Google Cloud project and enable the Gmail API

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a new project.
2. Navigate to **APIs & Services → Library**, search for **Gmail API**, and enable it.
3. Navigate to **APIs & Services → OAuth consent screen**.
   - Choose **External** user type.
   - Fill in app name, support email, and developer contact (any values work for personal use).
   - Add the scope `https://www.googleapis.com/auth/gmail.send`.
   - Under **Test users**, add the Gmail address you will send from.
   - Save. You do not need to publish the app — keeping it in Testing is fine for personal use (refresh tokens stay valid indefinitely while in Testing as long as you are a listed test user).
4. Navigate to **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
   - Application type: **Desktop app**.
   - Name it anything (e.g., `science-briefer`).
   - Download the JSON — you need `client_id` and `client_secret` from it.

### 3. Get a refresh token

Run this script once from your terminal. It opens a browser to authorize your Gmail account and prints a refresh token you save in `.env`.

```bash
python3 - <<'EOF'
import urllib.parse, urllib.request, json, webbrowser, http.server

CLIENT_ID     = input("Client ID: ").strip()
CLIENT_SECRET = input("Client Secret: ").strip()
REDIRECT_URI  = "http://localhost:8080"
SCOPE         = "https://www.googleapis.com/auth/gmail.send"

auth_url = (
    "https://accounts.google.com/o/oauth2/v2/auth?"
    + urllib.parse.urlencode({
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPE,
        "access_type":   "offline",
        "prompt":        "consent",
    })
)

print("\nOpening browser. If it opens the wrong Google account, copy the URL into an incognito window.\n")
print(auth_url)
webbrowser.open(auth_url)

code = input("\nPaste the 'code' parameter from the redirect URL: ").strip()

data = urllib.parse.urlencode({
    "code":          code,
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri":  REDIRECT_URI,
    "grant_type":    "authorization_code",
}).encode()

req = urllib.request.Request(
    "https://oauth2.googleapis.com/token", data=data, method="POST"
)
with urllib.request.urlopen(req) as resp:
    tokens = json.loads(resp.read())

print("\nRefresh token:", tokens.get("refresh_token", "(none — re-run with prompt=consent)"))
EOF
```

After the browser authorization step, Google redirects to `http://localhost:8080?code=...`. Copy the `code` value from that URL and paste it when prompted.

### 4. Create your `.env` file

```bash
cp .env.example .env
```

Fill in all four values:

```
GMAIL_CLIENT_ID=<your client_id>
GMAIL_CLIENT_SECRET=<your client_secret>
GMAIL_REFRESH_TOKEN=<your refresh_token>
GMAIL_SENDER_EMAIL=<the Gmail address you authorized>
```

`.env` is gitignored and never committed.

### 5. Create your user config and profile

```bash
cp templates/user-config.json config/users/<yourname>.json
cp templates/user-profile.md  agents/users/<yourname>.md
```

Edit both files:

- **`config/users/<yourname>.json`** — set your recipient email(s), date window, result limits, and PubMed search queries.
- **`agents/users/<yourname>.md`** — describe your research focus, which journals to prioritize, and the curation criteria for each section.

Both files are gitignored and never committed.

### 6. Install the skills into Claude Code

Copy the `skills/` directory into your Claude Code skills folder:

```bash
cp -r skills/* ~/.claude/skills/
```

Or symlink it so edits to the repo are reflected immediately:

```bash
ln -s "$(pwd)/skills/search-and-fetch"    ~/.claude/skills/search-and-fetch
ln -s "$(pwd)/skills/curate-and-summarize" ~/.claude/skills/curate-and-summarize
ln -s "$(pwd)/skills/compose-email"        ~/.claude/skills/compose-email
ln -s "$(pwd)/skills/send-email"           ~/.claude/skills/send-email
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
export GMAIL_CLIENT_ID="<your client_id>"
export GMAIL_CLIENT_SECRET="<your client_secret>"
export GMAIL_REFRESH_TOKEN="<your refresh_token>"
export GMAIL_SENDER_EMAIL="<your sender address>"
```

These are stored encrypted in your project and are not committed to the repo.

The `send-email` skill sources `.env` if present, and falls back to the environment automatically — no changes to the skill are needed.

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
│   └── send-email/               # Gmail API delivery
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
- A pre-commit hook blocks accidental commits of email addresses or OAuth tokens.
- The Gmail OAuth scope is limited to `gmail.send` — the app cannot read your inbox.
