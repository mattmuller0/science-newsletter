# Profile — Your Name

## Who I am
PhD candidate in [field] at [institution]. One or two lines on the lab's focus.

## Primary research focus
- [Topic]: [what specifically]
- [Topic]: [what specifically]

## Adjacent interests
- [Interest]
- [Interest]

## Section I — Cardiovascular Research (≥2 criteria)
- Published in: [journals that signal quality to you] (never counts for preprints)
- Mechanistic or translational finding in [your disease area]
- Involves omics data
- Directly relevant to [your specific biology]
- Novel biomarker, risk model, or therapeutic target
Deprioritize: case reports, editorials, clinical trials with no mechanistic or omic arm

## Section II — Methodology Developments (≥1 criterion)
- New or benchmarked computational tool for [your data types]
- Single-cell or spatial atlas for [your tissues]
- Novel multi-modal integration strategy
Deprioritize: wet-lab methods, incremental extensions of established tools

## Section III — Frontier Machine Learning (≥1 criterion)
- New representation-learning paradigm (JEPA, world models, self-supervised objectives)
- Foundation model for [your data types] with a methodological contribution
- New architecture or training paradigm (state space models, flow matching, energy-based models)
- Plausibly transferable to [your data and problems]
Mostly from arXiv; preprints carry no penalty here.
Deprioritize: robotics or game applications with no transferable idea, LLM product evaluations

## Summary style
Dense technical prose for a graduate-level reader. Two sentences per paper (finding, then significance), plus a third only when it bears directly on [your active work, e.g. platelet results, ATAC-seq methods].

## Settings
Searches, sections and recipients for the briefing. Keep this as valid JSON inside the code block. Sections render in the order listed here and need a matching "Section" heading above.

```json
{
  "recipient_email": [
    "you@example.com"
  ],
  "date_window_days": 7,
  "max_results_per_search": 12,
  "section_targets": {
    "domain": {
      "min": 4,
      "max": 8,
      "title": "Cardiovascular Research"
    },
    "methods": {
      "min": 4,
      "max": 8,
      "title": "Methodology Developments"
    },
    "frontier_ml": {
      "min": 3,
      "max": 6,
      "title": "Frontier Machine Learning"
    }
  },
  "searches": [
    {
      "id": "A",
      "label": "Platelet biology",
      "query": "(platelet OR thrombocyte) AND (activation OR transcriptome OR proteome OR single-cell) AND (thrombosis OR atherosclerosis OR cardiovascular)"
    },
    {
      "id": "B",
      "label": "Multi-omics integration",
      "query": "(multi-omics OR multiomics OR integrative omics) AND (cardiovascular OR immune OR vascular)"
    }
  ],
  "preprints": {
    "biorxiv": {
      "feeds": [
        {
          "id": "R1",
          "server": "biorxiv",
          "category": "bioinformatics"
        },
        {
          "id": "R2",
          "server": "medrxiv",
          "category": "cardiovascular medicine",
          "keep_all": true
        }
      ],
      "keywords": [
        "platelet*",
        "multi-omic*",
        "foundation model*",
        "self-supervised",
        "JEPA"
      ]
    },
    "arxiv": {
      "max_results_per_search": 30,
      "searches": [
        {
          "id": "X1",
          "label": "JEPA and predictive representation learning",
          "query": "(abs:JEPA OR abs:\"joint embedding predictive\" OR abs:\"latent prediction\") ANDNOT (cat:cs.RO)"
        }
      ]
    }
  }
}
```
