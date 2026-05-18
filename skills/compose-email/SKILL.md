---
name: compose-email
description: Render curated Section I and Section II paper lists into a fully styled HTML email; output only the subject string and html_body string
type: rigid
tools: []
---

# Skill: Compose Email

## Overview
This skill is **rigid** — produce HTML that exactly matches `template.html` in this directory. Do not alter colors, fonts, layout structure, or inline style values. Consistency across weekly issues is the goal.

**Inputs required in context before starting:**
- Section I paper list with summaries (from `curate-and-summarize`)
- Section II paper list with summaries (from `curate-and-summarize`)
- Today's date
- Total paper count

**Template file:** `skills/compose-email/template.html` — use this as the base; substitute all `{{TOKEN}}` placeholders.

**Output:** Exactly two values — `subject` (string) and `html_body` (complete HTML string). Nothing else.

---

## Subject line

Format:
```
Weekly Science Briefing — {Month} {D}, {YYYY} ({N} papers)
```

**Example:**
```
Weekly Science Briefing — May 6, 2026 (13 papers)
```

---

## Token substitution reference

| Token | Value | Example |
|-------|-------|---------|
| `{{DATE_LONG}}` | Full date, no leading zero | `May 6, 2026` |
| `{{N}}` | Total paper count (Section I + II) | `13` |
| `{{SECTION_I_TITLE}}` | `section_targets.cardiovascular.title` from config | `Cardiovascular Research` |
| `{{SECTION_II_TITLE}}` | `section_targets.methodology.title` from config | `Methodology Developments` |
| `{{PAPER_TITLE}}` | Title-case, no trailing period | `CAMK2D Causes Heart Failure in Mice with RBM20 Cardiomyopathy` |
| `{{DOI}}` | DOI string only, no URL prefix | `10.1038/s44161-026-00818-2` |
| `{{AUTHORS}}` | Last FM et al. — or both names if exactly 2 | `van den Hoogenhof MMG et al.` |
| `{{JOURNAL}}` | Journal name as returned by PubMed | `Nature Cardiovascular Research` |
| `{{DATE_MONTH_YEAR}}` | Month + year only | `May 2026` |
| `{{SUMMARY}}` | S1 + S2 [+ S3] as one paragraph | *(see example below)* |

**Author format rule:** Use the last name + initials style. If a single author, use their name alone. If exactly two authors, list both (`Smith AB, Jones CD`). If three or more, use first author only with `et al.` (`van den Hoogenhof MMG et al.`).

**Important — HTML-encode special characters in all text fields:**
- `&` → `&amp;`
- `<` → `&lt;`, `>` → `&gt;`
- Greek letters: `δ` → `&delta;`, `α` → `&alpha;`, `β` → `&beta;`
- Middle dot: `·` → `&middot;`

---

## Repeat the paper block

The template contains one placeholder paper block per section. Repeat the block once per paper:

- **Section I:** Repeat the block between the Section I header and the Section II header.
- **Section II:** Repeat the block after the Section II header. For the **last** paper in Section II, remove `border-bottom:1px solid #e0e0e0;padding-bottom:28px;` from the table's inline style.

---

## Filled-in paper block example

Input from `curate-and-summarize`:
```
Title:   CAMK2D Causes Heart Failure in Mice with RBM20 Cardiomyopathy
Authors: van den Hoogenhof MMG et al.
Journal: Nature Cardiovascular Research
Date:    2026-05-04
DOI:     10.1038/s44161-026-00818-2
Summary: Pathogenic variants in RBM20, a cardiac splicing factor, cause severe
         dilated cardiomyopathy; this study demonstrates that CAMK2D is the
         downstream effector mediating RBM20-driven cardiac dysfunction in mice,
         identifying it as a cause-directed therapeutic target. The mechanistic
         specificity of CAMK2D activation downstream of aberrant splicing
         suggests that kinase inhibition could serve as a genotype-tailored
         treatment strategy in a patient population currently receiving only
         generic heart failure pharmacotherapy.
```

Rendered paper block:
```html
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;border-bottom:1px solid #e0e0e0;padding-bottom:28px;">
  <tr>
    <td>
      <p style="margin:0 0 4px;font-family:Georgia,serif;font-size:15px;font-weight:bold;"><a href="https://doi.org/10.1038/s44161-026-00818-2" style="color:#1a2e4a;text-decoration:none;">CAMK2D Causes Heart Failure in Mice with RBM20 Cardiomyopathy</a></p>
      <p style="margin:0 0 10px;color:#666666;font-size:11px;font-family:Arial,sans-serif;">van den Hoogenhof MMG et al. &nbsp;&nbsp;|&nbsp;&nbsp; Nature Cardiovascular Research, May 2026</p>
      <p style="margin:0;color:#333333;font-size:14px;line-height:1.7;font-family:Georgia,serif;">Pathogenic variants in RBM20, a cardiac splicing factor, cause severe dilated cardiomyopathy; this study demonstrates that CAMK2D (calcium/calmodulin-dependent protein kinase II&delta;) is the downstream effector mediating RBM20-driven cardiac dysfunction in mice, identifying it as a cause-directed therapeutic target. The mechanistic specificity of CAMK2D activation downstream of aberrant splicing suggests that kinase inhibition could serve as a genotype-tailored treatment strategy in a patient population currently receiving only generic heart failure pharmacotherapy.</p>
    </td>
  </tr>
</table>
```

---

## Output

Return exactly:
1. `subject` — the subject line string
2. `html_body` — the complete rendered HTML string, ready to pass to `brevo-send`

No other commentary. Do not summarize the papers again or explain what you produced.
