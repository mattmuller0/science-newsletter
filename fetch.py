#!/usr/bin/env python3
"""Collect this week's candidate papers for the science briefing.

Runs every search in a user config against PubMed (NCBI E-utilities), bioRxiv and
medRxiv (category feeds, keyword-filtered), and arXiv, then writes one deduplicated
JSON list. Standard library only; no API keys.

  python3 fetch.py --config config/matt.json --out output/candidates.json [--days 14]
"""

import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "science-newsletter/2.0"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RXIV = "https://api.biorxiv.org/details/{server}/{d0}/{d1}/{cursor}/json?category={cat}"
ARXIV = "https://export.arxiv.org/api/query"
ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
EXCLUDED_TYPES = {"Letter", "Editorial", "Comment", "Case Reports", "Published Erratum",
                  "Retraction of Publication", "Retracted Publication", "News"}
ABSTRACT_CHARS = 900


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))


def authors(names):
    """Names as 'Jane A. Smith' or 'Smith, J. A.' -> 'Smith JA et al.'"""
    names = [n.strip() for n in names if n and n.strip()]

    def short(n):
        if "," in n:
            last, first = [p.strip() for p in n.split(",", 1)]
        else:
            *first, last = n.split()
            first = " ".join(first)
        return f"{last} {''.join(p[0] for p in re.split(r'[\s.-]+', first) if p)}".strip()

    if not names:
        return "Unknown"
    if len(names) <= 2:
        return ", ".join(short(n) for n in names)
    return f"{short(names[0])} et al."


def squash(s, n=None):
    s = " ".join((s or "").split())
    return s[:n] if n else s


def norm_title(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


def paper(**kw):
    kw.setdefault("doi", "")
    kw["abstract"] = squash(kw.get("abstract"), ABSTRACT_CHARS)
    kw["title"] = squash(kw["title"]).rstrip(".")
    return kw


# ── PubMed ──────────────────────────────────────────────────────────────────

def pubmed(cfg, d0, d1, log):
    hits = {}
    for s in cfg.get("searches", []):
        q = urllib.parse.urlencode({
            "db": "pubmed", "term": s["query"], "retmode": "json", "sort": "pub_date",
            "retmax": cfg.get("max_results_per_search", 12), "datetype": "pdat",
            "mindate": d0.strftime("%Y/%m/%d"), "maxdate": d1.strftime("%Y/%m/%d")})
        try:
            ids = json.loads(get(f"{EUTILS}/esearch.fcgi?{q}"))["esearchresult"]["idlist"]
            log.append(f"PubMed {s['id']} ({s.get('label', '')}): {len(ids)}")
        except Exception as e:
            log.append(f"PubMed {s['id']}: FAILED ({e})")
            ids = []
        for pmid in ids:
            hits.setdefault(pmid, []).append(s["id"])
        time.sleep(0.4)  # stay under 3 requests/s without an API key

    out, dropped, pmids = [], 0, list(hits)
    for i in range(0, len(pmids), 200):
        q = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids[i:i + 200]), "retmode": "xml"})
        root = ET.fromstring(get(f"{EUTILS}/efetch.fcgi?{q}"))
        for art in root.iter("PubmedArticle"):
            pmid = art.findtext(".//PMID")
            types = {t.text for t in art.iter("PublicationType")}
            abstract = " ".join("".join(a.itertext()) for a in art.iter("AbstractText"))
            if not abstract.strip() or types & EXCLUDED_TYPES:
                dropped += 1
                continue
            doi = next((x.text for x in art.iter("ArticleId") if x.get("IdType") == "doi"), "") or ""
            pd = art.find(".//JournalIssue/PubDate")
            date = " ".join(filter(None, [pd.findtext("Year"), pd.findtext("Month")])) if pd is not None else ""
            names = [f"{a.findtext('LastName')}, {a.findtext('ForeName') or a.findtext('Initials') or ''}"
                     for a in art.iter("Author") if a.findtext("LastName")]
            out.append(paper(
                id=f"PMID:{pmid}", source="pubmed", doi=doi,
                url=f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                title="".join(art.find(".//ArticleTitle").itertext()),
                venue=art.findtext(".//Journal/Title") or "", authors=authors(names),
                date=date or art.findtext(".//ArticleDate/Year") or "", abstract=abstract,
                types=sorted(types), searches=hits[pmid]))
        time.sleep(0.4)
    log.append(f"PubMed: {len(pmids)} unique PMIDs, {dropped} dropped (no abstract or excluded type)")
    return out


# ── bioRxiv / medRxiv ───────────────────────────────────────────────────────

def rxiv(cfg, d0, d1, log):
    kws = [(k, re.compile(rf"\b{re.escape(k).replace(chr(92) + '*', r'\w*')}\b", re.I))
           for k in cfg.get("keywords", [])]
    out = []
    for f in cfg.get("feeds", []):
        cursor = seen = kept = 0
        while True:
            url = RXIV.format(server=f["server"], d0=d0, d1=d1, cursor=cursor,
                              cat=urllib.parse.quote(f["category"].replace(" ", "_")))
            try:
                data = json.loads(get(url))
            except Exception as e:
                log.append(f"{f['server']}/{f['category']}: FAILED ({e})")
                break
            coll = data.get("collection", [])
            for r in coll:
                seen += 1
                text = f"{r.get('title', '')} {r.get('abstract', '')}"
                if str(r.get("version")) != "1":
                    continue  # skip revisions of older preprints
                if not f.get("keep_all") and not any(p.search(text) for _, p in kws):
                    continue
                kept += 1
                out.append(paper(
                    id=r["doi"], source=f["server"], doi=r["doi"], url=f"https://doi.org/{r['doi']}",
                    title=r.get("title", ""), venue=f"{'bioRxiv' if f['server'] == 'biorxiv' else 'medRxiv'} preprint",
                    authors=authors(r.get("authors", "").split(";")), date=r.get("date", ""),
                    abstract=r.get("abstract", ""), types=["Preprint"], searches=[f["id"]]))
            cursor += len(coll)
            total = int((data.get("messages") or [{}])[0].get("total", 0) or 0)
            if not coll or cursor >= total:
                break
        log.append(f"{f['server']}/{f['category']} ({f['id']}): {seen} scanned, {kept} kept")
    return out


# ── arXiv ───────────────────────────────────────────────────────────────────

def arxiv(cfg, d0, d1, log):
    out, window = [], f"submittedDate:[{d0:%Y%m%d}0000 TO {d1:%Y%m%d}2359]"
    for i, s in enumerate(cfg.get("searches", [])):
        if i:
            time.sleep(3)  # arXiv API etiquette
        q = urllib.parse.urlencode({"search_query": f"({s['query']}) AND {window}",
                                    "max_results": cfg.get("max_results_per_search", 30),
                                    "sortBy": "submittedDate", "sortOrder": "descending"})
        try:
            entries = ET.fromstring(get(f"{ARXIV}?{q}")).findall("a:entry", ATOM)
        except Exception as e:
            log.append(f"arXiv {s['id']}: FAILED ({e})")
            continue
        for e in entries:
            aid = re.sub(r"v\d+$", "", e.findtext("a:id", "", ATOM).rsplit("/abs/", 1)[-1])
            cat = e.find("arxiv:primary_category", ATOM)
            out.append(paper(
                id=f"arXiv:{aid}", source="arxiv", doi=e.findtext("arxiv:doi", "", ATOM),
                url=f"https://arxiv.org/abs/{aid}", title=e.findtext("a:title", "", ATOM),
                venue=f"arXiv preprint ({cat.get('term') if cat is not None else 'arXiv'})",
                authors=authors([a.findtext("a:name", "", ATOM) for a in e.findall("a:author", ATOM)]),
                date=e.findtext("a:published", "", ATOM)[:10], abstract=e.findtext("a:summary", "", ATOM),
                types=["Preprint"], searches=[s["id"]]))
        log.append(f"arXiv {s['id']} ({s.get('label', '')}): {len(entries)}")
    return out


def merge(papers):
    """One entry per id; a preprint whose DOI or title is already in PubMed is dropped."""
    by_id, published = {}, set()
    for p in papers:
        if p["source"] == "pubmed":
            published |= {p["doi"].lower(), norm_title(p["title"])} - {""}
    for p in papers:
        if p["source"] != "pubmed" and ({p["doi"].lower(), norm_title(p["title"])} & published):
            continue
        if p["id"] in by_id:
            by_id[p["id"]]["searches"] = sorted(set(by_id[p["id"]]["searches"]) | set(p["searches"]))
        else:
            by_id[p["id"]] = p
    return list(by_id.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--days", type=int, help="override date_window_days")
    a = ap.parse_args()

    cfg = json.load(open(a.config))
    d1 = dt.date.today()
    d0 = d1 - dt.timedelta(days=a.days or cfg.get("date_window_days", 7))
    log, papers = [f"Window: {d0} to {d1}"], []
    papers += pubmed(cfg, d0, d1, log)
    pre = cfg.get("preprints", {})
    if pre.get("biorxiv"):
        papers += rxiv(pre["biorxiv"], d0, d1, log)
    if pre.get("arxiv"):
        papers += arxiv(pre["arxiv"], d0, d1, log)
    merged = merge(papers)

    json.dump(merged, open(a.out, "w"), indent=1)
    counts = {}
    for p in merged:
        counts[p["source"]] = counts.get(p["source"], 0) + 1
    print("\n".join(log))
    print(f"Candidates: {len(merged)} ({', '.join(f'{k} {v}' for k, v in counts.items())}) -> {a.out}")
    sys.exit(2 if any("FAILED" in line for line in log) else 0)


if __name__ == "__main__":
    main()
