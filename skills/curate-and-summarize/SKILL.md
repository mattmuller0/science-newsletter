---
name: curate-and-summarize
description: Score and classify filtered papers against the user research profile, select final sets for two sections, and write dense technical summaries
type: rigid
tools: [TodoWrite]
---

# Skill: Curate and Summarize

## Overview
This skill is **rigid** — apply the scoring criteria exactly as written in the user profile. Do not substitute judgment for criteria.

**Inputs required in context before starting:**
- Filtered paper list from `search-and-fetch`
- User profile (`agents/users/<user>.md`) — Section I criteria, Section II criteria, summary style
- `config.section_targets` — `{cardiovascular: {min, max}, methodology: {min, max}}`

**Output:** Two labeled paper lists with summaries, passed to `compose-email`.

---

## Checklist
Create these todos before starting:
- [ ] Score and classify every candidate
- [ ] Select final Section I set
- [ ] Select final Section II set
- [ ] Check fallback condition
- [ ] Write summaries for all selected papers

---

## Step 1 — Score and classify every candidate

For **each paper**, evaluate against both section criteria from the user profile. Assign a section.

**Section I (≥2 criteria must match):**
- Published in a listed prestige journal (Circulation, JACC, NEJM, Nature Medicine, Lancet, Nature, Nat Cardiovasc Res, Circ Res, JAMA, Eur Heart J)
- Reports a mechanistic finding (not purely clinical outcome or procedural)
- Involves omics data (genomics, transcriptomics, proteomics, metabolomics, epigenomics)
- Directly relevant to platelet biology, thrombosis, or atherosclerosis
- Presents a novel biomarker, risk model, or therapeutic target

**Section II (≥1 criterion must match):**
- Introduces or benchmarks a computational tool for omics analysis
- Presents a single-cell or spatial atlas relevant to cardiovascular or hematopoietic biology
- Describes a novel integration strategy for multi-modal data
- Applies ML/DL to genomics, transcriptomics, or clinical signals in a technically novel way
- Relevant to methods the user actively uses (ATAC-seq analysis, scRNA-seq, proteomics pipelines, multi-omics integration)

A paper qualifying for both sections goes to whichever it fits more strongly.

**Deprioritize (exclude unless nothing better exists):**
- Case reports, editorials, letters (should already be filtered — skip if found)
- Purely clinical trial results with no mechanistic arm
- Review articles (include only if exceptionally comprehensive and published in a top journal)
- Procedural/surgical technique papers
- Papers with no clear connection to cardiovascular, hematopoietic, or relevant computational biology

**Example scoring:**

| PMID | Title snippet | Section I hits | Section II hits | Assignment |
|------|--------------|---------------|----------------|------------|
| 42082791 | CAMK2D / RBM20 HF | Nat Cardiovasc Res ✓, mechanistic ✓ → 2 | — | Section I |
| 42081463 | IL-4 / GPVI platelet | mechanistic ✓, platelet ✓ → 2 | — | Section I |
| 42086590 | scRNA metabolic labeling zebrafish heart | — | sc method ✓, cardiac atlas ✓ → 2 | Section II |
| 42069610 | scRNA-seq megakaryocytes | — | sc atlas hematopoietic ✓ → 1 | Section II |
| 42085153 | Pineal gland multiomics | — | — (not CV/hematopoietic) | Exclude |
| 42081720 | Lung cancer ginsenoside | — | — (not relevant) | Exclude |

---

## Step 2 — Select final sets

**Section I:** Select up to `max` papers, ranked by:
1. Journal prestige (Nat Med > Circ > Nat Cardiovasc Res > Blood > PNAS > Nature Comms > JAHA > others)
2. Direct relevance to the user's primary research focus (per user profile)
3. Novelty of finding (mechanistic discovery > method application > biomarker report)

**Section II:** Select up to `max` papers, ranked by:
1. Methodological novelty (new method > improved method > application of existing)
2. Applicability to the user's active toolkit (per user profile)
3. Dataset scope (larger atlas > smaller study)

If either section ends up **below its `min` target**, note this explicitly in the output header. Do not inflate either section with lower-quality papers.

---

## Step 3 — Fallback check

If the **total selected papers < 5**, do not proceed to summaries. Instead, output:

```
FALLBACK REQUIRED: Only {N} papers selected after curation across both sections.
Requesting date window expansion to 14 days.
Re-run search-and-fetch with date_window_days: 14 before continuing.
```

Return control to the orchestration agent.

---

## Step 4 — Write summaries

For each selected paper, write following the user profile style:

**Structure:**
- **S1** (required): Core finding + experimental or computational approach. One sentence. Lead with the biological or computational result, not the study design.
- **S2** (required): Methodological significance or translational relevance. One sentence.
- **S3** (optional): Add only when the paper has direct, specific relevance to the user's active work — a platelet-specific result, a new ATAC-seq or scRNA-seq method, a multi-omics integration approach, or a PRS method. One sentence.

**Style rules:**
- No hype language: never use "groundbreaking", "revolutionary", "landmark", "first-ever"
- Precise scientific vocabulary; assume a graduate-level reader
- Render as a single paragraph (S1 + S2 [+ S3] run together, no line breaks between sentences)

**Example summary (PMID 42081463 — Section I):**

> IL-4, an anti-inflammatory cytokine, directly binds platelet glycoprotein VI (GPVI) and suppresses thrombosis by dampening downstream platelet activation signaling, revealing an unexpected anti-thrombotic role for a cytokine studied primarily in allergic and Th2 immune contexts. This finding identifies GPVI as a molecular interface between inflammatory cytokine signaling and platelet function, with direct implications for understanding thromboinflammation in cardiovascular and immune-mediated disease. GPVI is a key platelet collagen receptor and high-priority therapeutic target candidate; IL-4-mediated inhibition of its signaling may inform novel anti-thrombotic strategies that exploit immune-vascular crosstalk.

**Example summary (PMID 42086590 — Section II):**

> In vivo metabolic labeling of newly synthesized RNA combined with single-cell sequencing captures the earliest transcriptional responses to cardiac injury in the regenerating zebrafish heart, resolving rapid gene expression dynamics invisible to standard scRNA-seq which cannot distinguish new from pre-existing transcripts. The approach is broadly applicable to systems where rapid transcriptional reprogramming drives a biological response, including mammalian cardiac remodeling and platelet activation upon vascular injury.

---

## Output format

Report this header first:
```
Curation complete: {N_I} Section I papers, {N_II} Section II papers ({N_total} total).
[WARN: Section I below minimum ({N_I} < {min_I})] ← only if applicable
```

Then two labeled lists:

```
## Section I — Cardiovascular · Mechanistic · Translational

**{Title}**
{Authors} | {Journal} | {Date} | DOI: {doi}
{Summary — S1 + S2 [+ S3] as one paragraph}

**{Title}**
...

## Section II — Computational Methods · Atlases · Single-Cell

**{Title}**
{Authors} | {Journal} | {Date} | DOI: {doi}
{Summary}

...
```

Pass both sections and the total paper count to `compose-email`.
