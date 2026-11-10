# Science Newsletter

An automated weekly research briefing delivered to your inbox. Claude searches PubMed for recent papers and bioRxiv, medRxiv and arXiv for recent preprints, curates them against your research profile, writes dense technical summaries, and sends a styled HTML email — all from a single prompt or on a recurring schedule.

---

## What it produces

Each issue contains the sections you configure (two or more). The defaults are:

**Section I — Cardiovascular Research** (or whatever domain you set)
Papers selected from high-prestige journals, prioritizing mechanistic findings and omics data. Each entry includes authors, journal, publication month, a DOI link, and a 2–3 sentence technical summary.

**Section II — Methodology Developments**
Computational methods papers, single-cell and spatial atlases, and ML/genomics tools relevant to your active toolkit.

**Section III — Frontier Machine Learning** (optional)
New representation-learning paradigms (JEPA, world models, self-supervised objectives), foundation models for omics and clinical data, and new architectures or training methods, mostly from arXiv.

Preprints appear in any section they qualify for and are labeled with their server (for example "bioRxiv preprint" or "arXiv preprint (cs.LG)").

Example entry:

> **Inhibiting Thromboinflammation via Interleukin-4 Binding to Platelet Glycoprotein VI and Suppression of Thrombosis**
> Lin S et al.  |  Blood, May 2026
>
> IL-4 directly binds platelet glycoprotein VI (GPVI) and suppresses thrombosis by dampening downstream platelet activation signaling, revealing an unexpected anti-thrombotic role for a cytokine studied primarily in allergic and Th2 immune contexts. This finding identifies GPVI as a molecular interface between inflammatory cytokine signaling and platelet function, with direct implications for understanding thromboinflammation in cardiovascular disease.

---

## How it works

1. **Search** — Configurable PubMed queries run in parallel subagents, each scoped to a date window (default: last 7 days). At the same time `scripts/fetch_preprints.py` pulls bioRxiv and medRxiv category feeds (keyword-filtered) and runs configurable arXiv queries over the same window.
2. **Curate** — Papers are deduplicated (a preprint already in PubMed is dropped in favor of the published version), filtered for article type and abstract presence, then scored against your research profile.
3. **Summarize** — Selected papers get 2–3 sentence technical summaries written to your specified style and audience level.
4. **Deliver** — A styled HTML email is composed and sent via the Gmail MCP tool. If sending fails, it is saved as a draft instead.

All search queries, section targets, curation criteria, and recipient addresses live in config files — nothing is hardcoded.

---

## Prerequisites

- A [Claude Code](https://claude.ai/code) account (or Claude Code CLI) with the Gmail and PubMed MCPs connected
- Python 3 (standard library only) and outbound access to api.biorxiv.org and export.arxiv.org for preprints

---

## Setup

### 1. Clone and enter the repo

```bash
git clone <your-fork-url>
cd science-newsletter
```

### 2. Connect the Gmail MCP

In your Claude Code project settings, enable the **Gmail** and **PubMed** MCPs. Gmail lets Claude send the briefing from your account — no API keys or credentials needed. The bioRxiv MCP is optional; it is only used as a fallback if the bioRxiv API cannot be reached.

### 3. Create your user config and profile

```bash
cp templates/user-config.json config/users/<yourname>.json
cp templates/user-profile.md  agents/users/<yourname>.md
```

Edit both files:

- **`config/users/<yourname>.json`** — set your recipient email(s), date window, result limits, sections, PubMed search queries, and the optional `preprints` block (bioRxiv/medRxiv feeds and keywords, arXiv queries).
- **`agents/users/<yourname>.md`** — describe your research focus, which journals to prioritize, and the curation criteria for each section.

Both files are gitignored and never committed.

### 5. Install the skills into Claude Code

Copy the `skills/` directory into your Claude Code skills folder:

```bash
cp -r skills/* ~/.claude/skills/
```

Or symlink it so edits to the repo are reflected immediately:

```bash
ln -s "$(pwd)/skills/search-and-fetch"     ~/.claude/skills/search-and-fetch
ln -s "$(pwd)/skills/curate-and-summarize" ~/.claude/skills/curate-and-summarize
ln -s "$(pwd)/skills/compose-email"        ~/.claude/skills/compose-email
ln -s "$(pwd)/skills/gmail-send"           ~/.claude/skills/gmail-send
```

---

## Running manually

Open Claude Code in the project root and send:

```
Run agents/science-briefer.md for user <yourname>.
```

Claude will execute all steps end-to-end and confirm the sent Gmail message ID when done.

---

## Running as a weekly routine on claude.ai/code

Claude.ai/code supports scheduled routines that run Claude automatically on a cadence. No credentials are needed — the Gmail MCP handles authentication.

### Create a routine

In your claude.ai/code project, create a new routine with:

- **Schedule**: weekly (e.g., every Monday at 8 AM)
- **Prompt**:

```
Run agents/science-briefer.md for user <yourname>.
```

Claude will search, curate, compose, and send the briefing on schedule.

---

## Customization

| What to change | Where |
|----------------|-------|
| PubMed queries | `config/users/<you>.json` → `searches` array |
| Preprint feeds and keywords | `config/users/<you>.json` → `preprints.biorxiv` |
| arXiv queries | `config/users/<you>.json` → `preprints.arxiv.searches` |
| Date window (default 7 days) | `config/users/<you>.json` → `date_window_days` |
| Sections and papers per section | `config/users/<you>.json` → `section_targets` |
| Curation criteria | `agents/users/<you>.md` → one block per section |
| Summary style and tone | `agents/users/<you>.md` → Summary Tone and Style |
| Email template | `skills/compose-email/template.html` |
| Recipients | `config/users/<you>.json` → `recipient_email` (string or list) |

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
│   ├── search-and-fetch/         # PubMed search, preprint fetch, merge
│   ├── curate-and-summarize/     # Scoring, selection, and summarization
│   ├── compose-email/            # HTML email rendering
│   └── gmail-send/               # Send via Gmail MCP (draft fallback)
├── scripts/
│   └── fetch_preprints.py        # bioRxiv / medRxiv / arXiv fetcher (stdlib only)
├── templates/
│   ├── user-config.json          # Starter template for config/users/<name>.json
│   └── user-profile.md          # Starter template for agents/users/<name>.md
└── output/                       # Generated artifacts — gitignored
```

---

## Security notes

- User configs and profiles are gitignored — your email addresses and research identity stay local.
- No API keys or credentials are stored in the repo; Gmail access is handled entirely by the MCP.
