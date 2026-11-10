#!/usr/bin/env python3
"""Render the briefing email from the curated picks.

picks.json holds only what curation decides, the section and the summary for each
paper. Titles, authors, venues and links come from candidates.json, so they are
never retyped by hand.

  {"sections": [{"key": "cardiovascular",
                 "papers": [{"id": "PMID:42081463", "summary": "IL-4 binds..."}]}]}

  python3 render.py --config config/matt.md --candidates output/candidates.json \
      --picks output/picks.json --out output/email.html

Prints the subject line; writes the HTML body to --out.
"""

import argparse
import datetime as dt
import html
import json
import sys

from fetch import load_config

NUMERALS = ["I", "II", "III", "IV", "V", "VI"]
SOURCE_NAMES = {"pubmed": "PubMed (NLM/NCBI)", "biorxiv": "bioRxiv", "medrxiv": "medRxiv", "arxiv": "arXiv"}

PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Weekly Science Briefing</title></head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:Georgia,serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#1a2e4a;"><tr><td style="padding:28px 40px;">
<h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:normal;font-family:Georgia,serif;">Weekly Science Briefing</h1>
<p style="margin:6px 0 0;color:#a8c4e0;font-size:13px;font-family:Arial,sans-serif;"><strong>{date}</strong> &nbsp;&middot;&nbsp; {n} papers</p>
</td></tr></table>
<table width="100%" cellpadding="0" cellspacing="0"><tr><td style="padding:32px 40px;max-width:700px;">
{body}
<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:40px;border-top:1px solid #cccccc;padding-top:20px;"><tr><td>
<p style="margin:0;color:#999999;font-size:11px;font-family:Arial,sans-serif;line-height:1.6;">{footer}</p>
</td></tr></table>
</td></tr></table>
</body></html>"""

SECTION = """<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;{gap}"><tr>
<td style="border-left:4px solid #c0392b;padding-left:12px;"><h2 style="margin:0;font-size:13px;font-weight:normal;font-family:Arial,sans-serif;letter-spacing:1.5px;text-transform:uppercase;color:#c0392b;">Section {numeral} &mdash; {title}</h2></td>
</tr></table>"""

PAPER = """<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;{rule}"><tr><td>
<p style="margin:0 0 4px;font-family:Georgia,serif;font-size:15px;font-weight:bold;"><a href="{url}" style="color:#1a2e4a;text-decoration:none;">{title}</a></p>
<p style="margin:0 0 10px;color:#666666;font-size:11px;font-family:Arial,sans-serif;">{authors} &nbsp;&nbsp;|&nbsp;&nbsp; {venue}, {when}</p>
<p style="margin:0;color:#333333;font-size:14px;line-height:1.7;font-family:Georgia,serif;">{summary}</p>
</td></tr></table>"""


def month_year(date):
    for fmt in ("%Y-%m-%d", "%Y %b", "%Y"):
        try:
            return dt.datetime.strptime(date, fmt).strftime("%B %Y" if fmt != "%Y" else "%Y")
        except ValueError:
            pass
    return date


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for arg in ("--config", "--candidates", "--picks", "--out"):
        ap.add_argument(arg, required=True)
    a = ap.parse_args()

    targets = load_config(a.config)["section_targets"]
    papers = {p["id"]: p for p in json.load(open(a.candidates))}
    picks = {s["key"]: s["papers"] for s in json.load(open(a.picks))["sections"]}

    unknown = [k for k in picks if k not in targets] + \
              [x["id"] for s in picks.values() for x in s if x["id"] not in papers]
    if unknown:
        sys.exit(f"Unknown section keys or paper ids in picks: {unknown}")

    chosen = [(key, picks[key]) for key in targets if picks.get(key)]
    blocks, sources, total = [], set(), sum(len(ps) for _, ps in chosen)
    for i, (key, ps) in enumerate(chosen):
        blocks.append(SECTION.format(gap="margin-top:12px;" if i else "", numeral=NUMERALS[i],
                                     title=html.escape(targets[key]["title"])))
        for j, pick in enumerate(ps):
            p = papers[pick["id"]]
            sources.add(p["source"])
            last = i == len(chosen) - 1 and j == len(ps) - 1
            blocks.append(PAPER.format(
                rule="" if last else "border-bottom:1px solid #e0e0e0;padding-bottom:28px;",
                url=html.escape(p["url"]), title=html.escape(p["title"]),
                authors=html.escape(p["authors"]), venue=html.escape(p["venue"]),
                when=html.escape(month_year(p["date"])), summary=html.escape(pick["summary"])))

    names = [SOURCE_NAMES[s] for s in SOURCE_NAMES if s in sources]
    footer = f"Papers sourced from {', '.join(names[:-1]) + ' and ' + names[-1] if len(names) > 1 else names[0]}. "
    footer += "Dates reflect indexing or posting dates and may differ from journal publication dates. "
    if sources - {"pubmed"}:
        footer += "Preprints have not been peer reviewed. "
    footer += "This briefing was curated and composed by an AI assistant and has not been editorially reviewed."

    today = dt.date.today()
    date_long = f"{today:%B} {today.day}, {today.year}"
    open(a.out, "w").write(PAGE.format(date=date_long, n=total, body="\n".join(blocks), footer=html.escape(footer)))
    print(f"Weekly Science Briefing — {date_long} ({total} papers)")


if __name__ == "__main__":
    main()
