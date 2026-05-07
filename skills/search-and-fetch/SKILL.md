---
name: search-and-fetch
description: Execute all PubMed searches from the user config in parallel subagents, deduplicate the returned PMIDs, and fetch full metadata for every unique paper
type: rigid
tools: [Agent, ToolSearch, TodoWrite]
---

# Skill: Search and Fetch Papers

## Overview
This skill is **rigid** — follow every step exactly. Deviation breaks downstream skills.

**Inputs required in context before starting:**
- User config JSON (`config/users/<user>.json`) — provides `searches`, `date_window_days`, `max_results_per_search`
- Today's date

**Output:** A deduplicated, filtered list of paper metadata objects passed to `curate-and-summarize`.

---

## Checklist
Create these todos before starting:
- [ ] Resolve PubMed tool names
- [ ] Compute date window
- [ ] Dispatch parallel search subagents
- [ ] Deduplicate PMIDs
- [ ] Fetch metadata in parallel batches
- [ ] Filter and produce final list

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

## Step 5 — Filter

Drop any paper where:
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

## Output format

Pass a list of objects to `curate-and-summarize`. Each object:
```
{
  pmid:          "42081463",
  doi:           "10.1182/blood.2025031889",
  title:         "Inhibiting Thromboinflammation via...",
  journal:       "Blood",
  authors:       "Lin S et al.",
  date:          "2026-05-04",
  abstract:      "Inflammation and coagulation are intricately linked...",
  article_types: ["Journal Article"],
  source_searches: ["C"]
}
```

Also report: total PMIDs retrieved, duplicates removed, papers dropped in filter, **final count**.

**Example summary line:**
```
Searches: 10 dispatched, 9 returned results (A returned 0 — skipped)
PMIDs retrieved: 134 raw → 100 unique after dedup → 96 after filter
Passing 96 papers to curate-and-summarize.
```
