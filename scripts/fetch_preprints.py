#!/usr/bin/env python3
"""Fetch recent preprints from bioRxiv, medRxiv and arXiv for the science briefing.

Standard library only. Reads the `preprints` block of a user config
(config/users/<user>.json) and writes one JSON list of paper objects in the same
shape that search-and-fetch produces for PubMed papers, so curation treats every
source the same way.

bioRxiv / medRxiv: the public API has no keyword search, so each configured
category feed is pulled in full for the date window and then filtered with the
config's keyword list (unless the feed sets "keep_all": true). Only version 1
postings are kept, so revisions of older preprints do not resurface.

arXiv: each configured search runs against the arXiv API with a submittedDate
window appended at runtime. Requests are spaced 3 s apart per arXiv's API terms.

Usage:
  python3 scripts/fetch_preprints.py --config config/users/matt.json \
      --date-from 2026-11-03 --date-to 2026-11-10 --out output/preprints.json
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "science-newsletter/1.0 (weekly research briefing)"
BIORXIV_API = "https://api.biorxiv.org/details/{server}/{d0}/{d1}/{cursor}/json"
ARXIV_API = "https://export.arxiv.org/api/query"
ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def get(url, retries=3, timeout=60):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # network hiccups, 5xx
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))


def fmt_authors(names):
    """['Jane A. Smith', ...] or ['Smith, J. A.', ...] -> 'Smith JA et al.'"""
    names = [n.strip() for n in names if n and n.strip()]
    if not names:
        return "Unknown"

    def short(n):
        if "," in n:
            last, first = [p.strip() for p in n.split(",", 1)]
        else:
            parts = n.split()
            last, first = parts[-1], " ".join(parts[:-1])
        initials = "".join(p[0] for p in re.split(r"[\s.\-]+", first) if p)
        return f"{last} {initials}".strip()

    if len(names) == 1:
        return short(names[0])
    if len(names) == 2:
        return f"{short(names[0])}, {short(names[1])}"
    return f"{short(names[0])} et al."


def compile_keywords(words):
    pats = []
    for w in words:
        # word-boundary match, case-insensitive; '*' acts as a suffix wildcard
        body = re.escape(w).replace(r"\*", r"\w*")
        pats.append((w, re.compile(rf"\b{body}\b", re.I)))
    return pats


def fetch_rxiv(cfg, d0, d1, log):
    keywords = compile_keywords(cfg.get("keywords", []))
    out = []
    for feed in cfg.get("feeds", []):
        server, category = feed["server"], feed["category"]
        cat_param = urllib.parse.quote(category.replace(" ", "_"))
        cursor, seen, kept = 0, 0, 0
        while True:
            url = BIORXIV_API.format(server=server, d0=d0, d1=d1, cursor=cursor)
            url += f"?category={cat_param}"
            try:
                data = json.loads(get(url))
            except Exception as e:
                log.append(f"{server}/{category}: FAILED ({e})")
                break
            coll = data.get("collection", [])
            msg = (data.get("messages") or [{}])[0]
            total = int(msg.get("total", 0) or 0)
            for rec in coll:
                seen += 1
                if str(rec.get("version")) != "1":
                    continue
                text = f"{rec.get('title','')} {rec.get('abstract','')}"
                hits = [w for w, p in keywords if p.search(text)]
                if not feed.get("keep_all") and not hits:
                    continue
                kept += 1
                out.append({
                    "id": rec["doi"],
                    "source": server,
                    "doi": rec["doi"],
                    "url": f"https://doi.org/{rec['doi']}",
                    "title": " ".join(rec.get("title", "").split()),
                    "venue": f"{'bioRxiv' if server == 'biorxiv' else 'medRxiv'} preprint",
                    "authors": fmt_authors(rec.get("authors", "").split(";")),
                    "date": rec.get("date", ""),
                    "abstract": " ".join(rec.get("abstract", "").split())[:900],
                    "article_types": ["Preprint"],
                    "category": category,
                    "matched_keywords": hits,
                    "source_searches": [feed.get("id", f"{server}:{category}")],
                })
            cursor += len(coll)
            if not coll or cursor >= total:
                break
        log.append(f"{server}/{category}: {seen} postings scanned, {kept} kept")
    return out


def fetch_arxiv(cfg, d0, d1, log):
    out = []
    lo, hi = d0.replace("-", "") + "0000", d1.replace("-", "") + "2359"
    max_results = cfg.get("max_results_per_search", 40)
    for i, s in enumerate(cfg.get("searches", [])):
        if i:
            time.sleep(3)
        q = f"({s['query']}) AND submittedDate:[{lo} TO {hi}]"
        params = urllib.parse.urlencode({
            "search_query": q, "max_results": max_results,
            "sortBy": "submittedDate", "sortOrder": "descending",
        })
        try:
            root = ET.fromstring(get(f"{ARXIV_API}?{params}"))
        except Exception as e:
            log.append(f"arXiv {s['id']}: FAILED ({e})")
            continue
        entries = root.findall("a:entry", ATOM)
        for e in entries:
            aid = e.find("a:id", ATOM).text.rsplit("/abs/", 1)[-1]
            base = re.sub(r"v\d+$", "", aid)
            prim = e.find("arxiv:primary_category", ATOM)
            doi = e.find("arxiv:doi", ATOM)
            out.append({
                "id": f"arXiv:{base}",
                "source": "arxiv",
                "doi": doi.text if doi is not None else "",
                "url": f"https://arxiv.org/abs/{base}",
                "title": " ".join(e.find("a:title", ATOM).text.split()),
                "venue": f"arXiv preprint ({prim.get('term') if prim is not None else 'arXiv'})",
                "authors": fmt_authors([a.find("a:name", ATOM).text for a in e.findall("a:author", ATOM)]),
                "date": e.find("a:published", ATOM).text[:10],
                "abstract": " ".join(e.find("a:summary", ATOM).text.split())[:900],
                "article_types": ["Preprint"],
                "category": prim.get("term") if prim is not None else "",
                "matched_keywords": [],
                "source_searches": [s["id"]],
            })
        log.append(f"arXiv {s['id']} ({s.get('label','')}): {len(entries)} results")
    return out


def dedupe(papers):
    merged = {}
    for p in papers:
        key = p["id"].lower()
        if key in merged:
            m = merged[key]
            m["source_searches"] = sorted(set(m["source_searches"]) | set(p["source_searches"]))
            m["matched_keywords"] = sorted(set(m["matched_keywords"]) | set(p["matched_keywords"]))
        else:
            merged[key] = p
    return list(merged.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--date-from", required=True, help="YYYY-MM-DD")
    ap.add_argument("--date-to", required=True, help="YYYY-MM-DD")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg = json.load(open(args.config)).get("preprints", {})
    log, papers = [], []
    if cfg.get("biorxiv"):
        papers += fetch_rxiv(cfg["biorxiv"], args.date_from, args.date_to, log)
    if cfg.get("arxiv"):
        papers += fetch_arxiv(cfg["arxiv"], args.date_from, args.date_to, log)
    raw = len(papers)
    papers = dedupe(papers)

    with open(args.out, "w") as f:
        json.dump(papers, f, indent=1)
    for line in log:
        print(line)
    print(f"Preprints: {raw} raw -> {len(papers)} unique. Written to {args.out}")
    if any("FAILED" in l for l in log):
        sys.exit(2)


if __name__ == "__main__":
    main()
