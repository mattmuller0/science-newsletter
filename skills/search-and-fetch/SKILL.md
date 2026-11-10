---
name: search-and-fetch
description: Execute all PubMed searches from the user config in parallel subagents, fetch bioRxiv, medRxiv and arXiv preprints with scripts/fetch_preprints.py, deduplicate across sources, and produce one filtered candidate list
type: rigid
tools: [Agent, ToolSearch, TodoWrite, Bash]
---

# Skill: Search and Fetch Papers

## Overview
This skill is **rigid** — follow every step exactly. Deviation breaks downstream skills.

**Inputs required in context before starting:**
- User config JSON (`config/users/<user>.json`) — provides `searches`, `date_window_days`, `max_results_per_search`, and the optional `preprints` block
- Today's date

**Output:** A deduplicated, filtered list of paper metadata objects (peer-reviewed and preprint) passed to `curate-and-summarize`.

---

## Checklist
Create these todos before starting:
- [ ] Resolve PubMed tool names
- [ ] Compute date window
- [ ] Start the preprint fetch (Step 6) in the background
- [ ] Dispatch parallel search subagents
- [ ] Deduplicate PMIDs
- [ ] Fetch metadata in parallel batches
- [ ] Filter PubMed results
- [ ] Collect preprints and merge across sources

---

## Step 0 — Resolve PubMed tool names

Use a **single** `ToolSearch` call to find both tools at once:

```
ToolSearch query: "pubmed search_articles get_article_metadata"   max_results: 5
```

From the results, record:
- `SEARCH_TOOL` — the full name ending in `__search_articles`
- `METADATA_TOOL` — the full name ending in `__get_article_metadata`

Example: `mcp__<server-id>__search_articles`, `mcp__<server-id>__get_article_metadata`

Use these names verbatim in all subagent prompts. Pass them as literal strings — subagents must NOT run their own ToolSearch.

---

## Step 1 — Compute date window

Subtract `date_window_days` from today to get `date_from`. Format both as `YYYY/MM/DD`.

**Example** (today = 2026-05-06, window = 7 days):
```
date_from = "2026/04/29"
date_to   = "2026/05/06"
```

If the config has a `preprints` block, start Step 6 now (Bash, `run_in_background: true`) so it runs while the PubMed subagents work. It uses the same window in `YYYY-MM-DD` form.

---

## Step 2 — Dispatch parallel search subagents

Send **one Agent tool call per search entry** in `config.searches`, all in a single message. Do not wait for one to finish before dispatching the next.

Use **`model: haiku`** for every search subagent — they perform a single API call and need no reasoning.

**Subagent prompt template** (fill in all `{placeholders}`; `{SEARCH_TOOL}` is the resolved full tool name):

```
Call the tool {SEARCH_TOOL} with these exact parameters:
  query:       "{query} AND ("{date_from}"[Date - Publication] : "{date_to}"[Date - Publication])"
  max_results: {max_results}
  sort:        pub_date

Return ONLY a comma-separated list of PMIDs from the results. If empty, return: NONE
```

**Example subagent prompt for search C (Platelet biology):**
```
Call the tool mcp__<server-id>__search_articles with these exact parameters:
  query:       "(platelet OR thrombocyte) AND (activation OR aggregation OR ...) AND
                ("2026/04/29"[Date - Publication] : "2026/05/06"[Date - Publication])"
  max_results: 12
  sort:        pub_date

Return ONLY a comma-separated list of PMIDs from the results. If empty, return: NONE
```

**Example subagent return:**
```
PMIDs: 42081463, 42090450, 42086829, 41944092, 42087745, 42069812, ...
```

Collect all PMID lists. If a search returns 0 results, skip it silently — do not widen the window at this stage.

---

## Step 3 — Deduplicate

Merge all PMID lists. Remove duplicates. Track which search(es) each PMID appeared in (useful for curation context).

**Example:**
```
Search B → [42086979, 42082791, 42054694]
Search C → [42081463, 42082791, 42090450]   ← 42082791 is a duplicate
Search F → [42082791, 42089142]              ← 42082791 again

Deduplicated → [42086979, 42082791, 42054694, 42081463, 42090450, 42089142]
                                               ↑ kept once, appeared in B+C+F
```

---

## Step 4 — Fetch metadata in parallel batches

Split the deduplicated list into **batches of 10**. Dispatch one Agent call per batch, all in parallel (single message).

Use **`model: haiku`** for every metadata subagent — they perform API calls and format output, no reasoning required. Dispatch all batches in a **single message** (parallel tool calls).

**Subagent prompt template** (`{METADATA_TOOL}` is the resolved full tool name):
```
Call the tool {METADATA_TOOL} for each of these PMIDs: {pmid_1}, {pmid_2}, ..., {pmid_10}

For each article return exactly these fields:
  PMID, title, journal, authors (Last FM et al. if >2 authors), publication date,
  abstract first 300 chars (or "NO ABSTRACT" if absent), article_types, DOI.
```

**Example metadata record returned:**
```
PMID:          42081463
Title:         Inhibiting Thromboinflammation via Interleukin-4 Binding to
               Platelet Glycoprotein VI and Suppression of Thrombosis
Journal:       Blood
Authors:       Lin S et al.
Date:          2026-05-04
Abstract:      "Inflammation and coagulation are intricately linked. Although
               some studies have documented pro-inflammatory drivers..."
Article types: Journal Article
DOI:           10.1182/blood.2025031889
```

---

## Step 5 — Filter PubMed results

Drop any PubMed paper where:
- Abstract is null, empty, or "No abstract available"
- `article_types` contains any of: Letter, Editorial, Comment, Case Report, Published Erratum, Retraction

**Example drops:**
```
42054694 → Letter + Comment + no abstract    → DROP
42090345 → Editorial + no abstract           → DROP
42082792 → no abstract                       → DROP
42087745 → Case Report                       → DROP
```

---

## Step 6 — Fetch preprints (bioRxiv, medRxiv, arXiv)

Skip this step if the config has no `preprints` block.

Run from the repo root (start it in the background during Step 1, collect it here):

```bash
mkdir -p output
python3 scripts/fetch_preprints.py --config config/users/<user>.json \
    --date-from <YYYY-MM-DD> --date-to <YYYY-MM-DD> --out output/preprints.json
```

The script reads `preprints.biorxiv.feeds` (bioRxiv and medRxiv category feeds, keyword-filtered on title and abstract unless a feed sets `keep_all`) and `preprints.arxiv.searches` (arXiv API queries; the submission-date window is appended automatically). It keeps only version 1 postings, so revisions of old preprints do not resurface, and it writes objects already in the output format below. Its stdout reports per-feed counts; keep that for the summary line.

Load `output/preprints.json` with Bash (for example `python3 -c` printing id, venue, title and abstract per line) rather than reading the raw file into context.

**If the script exits non-zero**, its log names the failed feeds; everything else in the file is still valid. For each failed source, try once:
- bioRxiv/medRxiv: if a bioRxiv MCP tool is available (`ToolSearch` query "biorxiv search_preprints"), call `search_preprints` per failed feed with `date_from`/`date_to`, `server` and `category`, `limit: 100`, and apply the config keywords to titles and abstracts yourself.
- arXiv: run `WebSearch` with `site:arxiv.org` plus the search's key terms and the current month, and keep only results submitted inside the window.
If the fallback also fails, continue without that source and note it in the summary line. Never block the briefing on preprints.

**Merge with PubMed results.** Drop a preprint when its DOI matches a PubMed paper's DOI, or when its lower-cased title (punctuation removed) matches a PubMed title; the peer-reviewed version wins. Combine `source_searches` when merging.

---

## Output format

Pass one list of objects to `curate-and-summarize`, PubMed papers and preprints together. Each object:
```
{
  id:            "PMID:42081463",            // or a bioRxiv DOI, or "arXiv:2611.12137"
  source:        "pubmed",                    // pubmed | biorxiv | medrxiv | arxiv
  doi:           "10.1182/blood.2025031889", // may be empty for arXiv
  url:           "https://doi.org/10.1182/blood.2025031889",  // arXiv: https://arxiv.org/abs/<id>
  title:         "Inhibiting Thromboinflammation via...",
  venue:         "Blood",                     // journal name, or "bioRxiv preprint" / "arXiv preprint (cs.LG)"
  authors:       "Lin S et al.",
  date:          "2026-05-04",
  abstract:      "Inflammation and coagulation are intricately linked...",
  article_types: ["Journal Article"],          // ["Preprint"] for preprints
  source_searches: ["C"]
}
```

For PubMed papers, build `url` as `https://doi.org/<doi>` (or `https://pubmed.ncbi.nlm.nih.gov/<pmid>/` when there is no DOI) and set `venue` to the journal name.

Also report: PubMed PMIDs retrieved, duplicates removed, papers dropped in filter, preprints per source, cross-source duplicates removed, **final count**.

**Example summary line:**
```
PubMed: 11 searches dispatched, 10 returned results (A returned 0 — skipped)
PMIDs retrieved: 134 raw → 100 unique after dedup → 96 after filter
Preprints: bioRxiv 69, medRxiv 29, arXiv 81 → 176 after removing 3 already in PubMed
Passing 272 papers to curate-and-summarize.
```
