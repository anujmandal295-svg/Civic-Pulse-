"""BM25 retrieval over chunks; facet queries keep long documents within context."""
import re
from rank_bm25 import BM25Okapi

FACETS = ["who is eligible conditions criteria", "benefit amount rights entitlement",
          "last date deadline time limit penalty", "documents required how to apply procedure",
          "exemption exclusion offence prohibited obligation compliance"]

def tok(s): return re.findall(r"\w+", s.lower())

def select(chunks, max_all=40, per_facet=6):
    if len(chunks) <= max_all:
        return chunks
    bm = BM25Okapi([tok(c["text"]) for c in chunks])
    keep = set()
    for q in FACETS:
        scores = bm.get_scores(tok(q))
        keep.update(sorted(range(len(chunks)), key=lambda i: -scores[i])[:per_facet])
    return [chunks[i] for i in sorted(keep)]

def top(chunks, query, k=5):
    bm = BM25Okapi([tok(c["text"]) for c in chunks])
    s = bm.get_scores(tok(query))
    return [chunks[i] for i in sorted(range(len(chunks)), key=lambda i: -s[i])[:k]]
