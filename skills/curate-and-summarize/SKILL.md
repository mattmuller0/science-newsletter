---
name: curate-and-summarize
description: Score and classify candidate papers and preprints against the user research profile, select a final set for each configured section, and write dense technical summaries
type: rigid
tools: [TodoWrite]
---

# Skill: Curate and Summarize

## Overview
This skill is **rigid** — apply the scoring criteria exactly as written in the user profile. Do not substitute judgment for criteria.

**Inputs required in context before starting:**
- Candidate list from `search-and-fetch` (PubMed papers and preprints in one list)
- User profile (`agents/users/<user>.md`) — one criteria block per section, plus summary style
- `config.section_targets` — an ordered map of sections, each `{min, max, title}`. Sections are numbered in config order: the first key is Section I, the second Section II, the third Section III, and so on. The profile has a matching `## Section I`, `## Section II`, ... block for each.

**Output:** One labeled paper list per section, with summaries, passed to `compose-email`.

---

## Checklist
Create these todos before starting:
- [ ] Triage candidates by title
- [ ] Score and classify every shortlisted candidate
- [ ] Select the final set for each section
- [ ] Check fallback condition
- [ ] Write summaries for all selected papers

---

## Step 0 — Triage by title

The candidate list can run to a few hundred items. First pass on titles and venue alone: discard anything plainly outside every section's scope (unrelated organisms or diseases, non-biological robotics or vision tasks, pure clinical administration, LLM chat safety, and similar). Keep anything plausibly in scope for any section. Only shortlisted items get the full abstract-level scoring in Step 1.

---

## Step 1 — Score and classify every candidate

For **each shortlisted paper**, evaluate it against every section's criteria from the user profile and assign it to one section. Each profile section states its own threshold (for example "≥2 criteria" or "≥1 criterion"); apply it exactly.

A paper qualifying for more than one section goes to whichever it fits more strongly. A machine learning paper with a cardiovascular or omics application goes to the methods section unless its core contribution is the architecture or training paradigm itself, in which case it goes to the frontier ML section (when the config has one).

**Preprints** (`article_types: ["Preprint"]`) are eligible in every section and are scored against the same criteria. Journal-prestige criteria never count toward a preprint's threshold. When a preprint and a peer-reviewed paper are otherwise equal for a slot, the peer-reviewed paper wins, unless the profile says a section favors preprints.

**Deprioritize (exclude unless nothing better exists):**
- Case reports, editorials, letters (should already be filtered — skip if found)
- Purely clinical trial results or observational associations with no mechanistic, omic or methodological arm
- Review and survey articles (include only if exceptionally comprehensive and published in a top venue)
- Procedural/surgical technique papers
- Papers with no clear connection to any section's scope
- Anything the profile lists under a section's **Deprioritize** line

**Example scoring:**

| ID | Title snippet | Best fit | Hits | Assignment |
|----|--------------|----------|------|------------|
| PMID:42082791 | CAMK2D / RBM20 HF | I | Nat Cardiovasc Res ✓, mechanistic ✓ → 2 | Section I |
| PMID:42081463 | IL-4 / GPVI platelet | I | mechanistic ✓, platelet ✓ → 2 | Section I |
| PMID:42069610 | scRNA-seq megakaryocytes | II | sc atlas hematopoietic ✓ → 1 | Section II |
| bioRxiv 10.1101/… | VLM-guided gene activity from scATAC | II | ATAC method ✓, ML novel ✓ → 2 | Section II |
| arXiv:2611.12137 | Counterexamples for Gaussian-regularized JEPAs | III | JEPA theory ✓ → 1 | Section III |
| arXiv:2611.12676 | VLA adaptation, robotic chess | — | robotics, out of scope | Exclude |

---

## Step 2 — Select final sets

For each section, select up to its `max`.

**Domain sections** (biology or disease focused, e.g. Cardiovascular Research), ranked by:
1. Venue prestige (Nat Med > Circ > Nat Cardiovasc Res > Blood > PNAS > Nature Comms > JAHA > others; preprints rank below peer-reviewed venues here)
2. Direct relevance to the user's primary research focus (per user profile)
3. Novelty of finding (mechanistic discovery > method application > biomarker report)

**Methods sections** (computational tools, atlases, integration), ranked by:
1. Methodological novelty (new method > improved method > application of existing)
2. Applicability to the user's active toolkit (per user profile)
3. Dataset scope (larger atlas > smaller study)

**Frontier ML sections** (architectures, training paradigms, foundation models), ranked by:
1. Conceptual novelty of the method or the finding about it (new paradigm or result that changes how a method is understood > strong empirical advance > benchmark or application)
2. Plausible transfer to the user's data (omics, biosignals, clinical cohorts), per the profile
3. Rigor signals visible in the abstract (theory, ablations, scale of evaluation)

If any section ends up **below its `min` target**, note this explicitly in the output header. Do not inflate any section with lower-quality papers.

---

## Step 3 — Fallback check

If the **total selected papers < 5**, do not proceed to summaries. Instead, output:

```
FALLBACK REQUIRED: Only {N} papers selected after curation across all sections.
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
- **S3** (optional): Add only when the paper has direct, specific relevance to the user's active work, as the profile defines it. One sentence.

**Style rules:**
- No hype language: never use "groundbreaking", "revolutionary", "landmark", "first-ever"
- Precise scientific vocabulary; assume a graduate-level reader
- Render as a single paragraph (S1 + S2 [+ S3] run together, no line breaks between sentences)
- For preprints, do not describe results as established; phrase as "report", "propose", "show in their experiments"

**Example summary (PMID 42081463 — Section I):**

> IL-4, an anti-inflammatory cytokine, directly binds platelet glycoprotein VI (GPVI) and suppresses thrombosis by dampening downstream platelet activation signaling, revealing an unexpected anti-thrombotic role for a cytokine studied primarily in allergic and Th2 immune contexts. This finding identifies GPVI as a molecular interface between inflammatory cytokine signaling and platelet function, with direct implications for understanding thromboinflammation in cardiovascular and immune-mediated disease. GPVI is a key platelet collagen receptor and high-priority therapeutic target candidate; IL-4-mediated inhibition of its signaling may inform novel anti-thrombotic strategies that exploit immune-vascular crosstalk.

**Example summary (PMID 42086590 — Section II):**

> In vivo metabolic labeling of newly synthesized RNA combined with single-cell sequencing captures the earliest transcriptional responses to cardiac injury in the regenerating zebrafish heart, resolving rapid gene expression dynamics invisible to standard scRNA-seq which cannot distinguish new from pre-existing transcripts. The approach is broadly applicable to systems where rapid transcriptional reprogramming drives a biological response, including mammalian cardiac remodeling and platelet activation upon vascular injury.

---

## Output format

Report this header first:
```
Curation complete: {N_I} Section I, {N_II} Section II, {N_III} Section III papers ({N_total} total, {N_preprint} preprints).
[WARN: Section I below minimum ({N_I} < {min_I})] ← only if applicable, one line per section
```

Then one labeled list per section, in config order:

```
## Section I — {section title}

**{Title}**
{Authors} | {Venue} | {Date} | {url}
{Summary — S1 + S2 [+ S3] as one paragraph}

**{Title}**
...

## Section II — {section title}

...
```

Pass all sections, their titles, the total paper count and whether any preprints were included to `compose-email`.
