# Weekly Science Briefing

Instructions for Claude. Produce and send one user's weekly research briefing: fetch recent papers and preprints, pick the best for each section of their profile, summarize them, render the email, and send it with Gmail.

This normally runs as an unattended scheduled task. Make every decision yourself and do not ask questions. Work from the repo root.

## 1. Load the user's config and profile

Each user has two files: `<user>.json` (searches, sections, recipients) and `<user>.md` (what they care about, per-section criteria, summary style). They are personal, so they are never committed.

Look for them in this order and use the first place that has both:

1. `config/<user>.json` and `config/<user>.md` in this repo
2. Google Drive, in the folder `science-newsletter-config` (or the folder the task prompt names). Find the folder and then each file by title with `search_files`, fetch each with `download_file_content`, and copy the downloaded files to `config/<user>.json` and `config/<user>.md`. Do not use `read_file_content` for these; it can return empty text for plain-text files.

Check that the JSON parses. If either file can't be found, stop: do not fetch, compose or send anything, and report where you looked.

## 2. Fetch candidates

```bash
mkdir -p output
python3 fetch.py --config config/<user>.json --out output/candidates.json
```

This runs every PubMed search, bioRxiv/medRxiv feed and arXiv query in the config over the date window, drops PubMed items with no abstract or an excluded type (letters, editorials, case reports and similar), keeps only first versions of preprints, drops preprints already published in PubMed, and prints counts per search. It takes about a minute.

If it exits non-zero, the log names what failed and everything else in the file is still usable. If PubMed failed entirely, fall back to the PubMed connector (`search_articles`, then `get_article_metadata`) for the config's searches. If a preprint source failed, carry on without it and say so in the report. If fewer than about 30 candidates came back, rerun with `--days 14`.

## 3. Curate

The candidate list can be a few hundred items, so work in two passes rather than reading every abstract.

First, list `id | venue | title` for all candidates (a short `python3 -c` over the JSON) and discard anything plainly outside every section's scope. Then read the abstracts of what is left and assign each paper to at most one section.

Sections come from `section_targets` in the config, in order: the first is Section I, the second Section II, and so on. Each has a `min`, a `max` and a title, and the profile has a matching `## Section …` block with its criteria and threshold (for example "≥2 criteria"). Apply those criteria as written.

When choosing which papers make the cut:

- A paper that fits more than one section goes where it fits best. Machine learning applied to cardiovascular or omics data belongs in the methods section, unless the contribution is the architecture or training idea itself, in which case it belongs in the frontier ML section.
- Preprints are eligible everywhere and judged on the same criteria, except that journal-prestige criteria never count for them. At equal relevance a peer-reviewed paper beats a preprint, unless the profile says a section favors preprints.
- Rank domain sections by venue, then relevance to the user's primary focus, then novelty (mechanism over application over biomarker report). Rank methods sections by methodological novelty, then fit with the user's toolkit, then scope. Rank frontier ML sections by conceptual novelty, then plausible transfer to the user's data, then rigor visible in the abstract.
- Skip anything on a section's Deprioritize line, reviews unless exceptional, and pure clinical outcome reports with no mechanistic, omic or methodological angle.
- Take up to `max` per section. If a section falls short of `min`, leave it short rather than pad it, and mention it in the report.

## 4. Summarize

Write one paragraph per selected paper, following the profile's Summary Style:

- First sentence: the core finding and how it was obtained, leading with the result rather than the study design.
- Second sentence: why it matters methodologically or translationally (for frontier ML, what is new relative to prior approaches).
- Optional third sentence, only when the paper bears directly on the user's own work as the profile describes it.

Use precise terms for a graduate-level reader and no hype words ("groundbreaking", "revolutionary", "landmark", "first-ever"). For preprints, phrase results as reported, not established. Write plain text; the renderer handles HTML escaping.

## 5. Render

Write `output/picks.json` with each section's config key and, per paper, only its `id` from candidates.json and your summary:

```json
{"sections": [
  {"key": "cardiovascular", "papers": [{"id": "PMID:42081463", "summary": "..."}]},
  {"key": "frontier_ml",    "papers": [{"id": "arXiv:2611.12137", "summary": "..."}]}
]}
```

Then:

```bash
python3 render.py --config config/<user>.json --candidates output/candidates.json \
    --picks output/picks.json --out output/email.html
```

It prints the subject line and writes the HTML, pulling titles, authors, venues and links from the candidates so none of them are retyped. If it reports an unknown id or section key, fix `picks.json` and rerun.

## 6. Send

Call the Gmail `send_message` tool once, with `to` set to the config's `recipient_email` (as a list), `subject` set to the printed subject line, and `htmlBody` set to the full contents of `output/email.html`. This is a send to the user's own configured address, so no confirmation is needed.

If the send returns an error, do not retry it, since a failed-looking call can still deliver and a retry risks a duplicate. Instead create one draft with `create_draft` using the same fields. If no send tool is available, go straight to the draft.

## 7. Report

Finish with a few lines: candidates per source, papers per section (noting any below `min`), any source that failed, and the Gmail message ID (or the send error and the draft ID).
