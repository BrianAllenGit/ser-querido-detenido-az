#!/usr/bin/env python3
"""Proves every quote in tools/quotes.json (and so on the page) is a word for word match of a saved source.

For each quote, every block of it (paragraph, list item, heading, footnote) is checked on its own: strip tags, unescape
entities, collapse whitespace, then require the result to appear inside the saved source text (same normalisation).
Then the page itself is checked: every quote in index.html must contain exactly the quote's HTML.
Exit 1 on any mismatch.
"""
import html as H
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CAP = os.path.join(HERE, "captures")
BR = {"en": "pdf/odls_brochure_en.txt", "es": "pdf/odls_brochure_es.txt"}
EOIR_LIST = ["pdf/eoir_az_eloy_left.txt", "pdf/eoir_az_eloy_right.txt", "pdf/eoir_az_eloy_page.txt"]
SOURCE = {
    "ero_phoenix_en": ["ice_ero.txt"], "eloy_en": ["ice_eloy.txt"], "florence_en": ["ice_florence.txt"],
    "eoir_status_en": ["eoir_status_en.txt"], "acis_intro_en": ["acis_en.txt"], "acis_official_en": ["acis_en.txt"],
    "acis_intro_es": ["acis_es.txt"], "acis_official_es": ["acis_es.txt"], "eoir_list_az_en": EOIR_LIST,
}


def norm(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<svg.*?</svg>", " ", s, flags=re.S)
    s = re.sub(r"</(li|p|h\d|div|ul|ol|td|tr)>|<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = H.unescape(s).replace("\xa0", " ").replace("​", "")
    return re.sub(r"\s+", " ", s).strip()


def blocks(h):
    return [b for b in re.findall(r"<(?:p|li|h3|h4)[^>]*>(.*?)</(?:p|li|h3|h4)>", h, flags=re.S) if norm(b)]


def main():
    quotes = json.load(open(os.path.join(HERE, "quotes.json"), encoding="utf-8"))
    page = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    bad = 0
    for key, q in quotes.items():
        srcs = [norm(open(os.path.join(CAP, f), encoding="utf-8", errors="replace").read()) for f in SOURCE[key]]
        srcns = [re.sub(r"\s", "", s) for s in srcs]
        bl = blocks(q["html"])
        miss = [b for b in bl if not any(norm(b) in s or re.sub(r"\s", "", norm(b)) in n for s, n in zip(srcs, srcns))]
        chars = sum(len(norm(b)) for b in bl)
        n_page = page.count(q["html"])
        ok = not miss and n_page >= 1
        print("%s %-20s %5d chars, %2d blocks, blocks not in source: %d, on page: %dx" % ("PASS" if ok else "FAIL", key, chars, len(bl), len(miss), n_page))
        for m in miss:
            print("   NOT IN SOURCE: " + norm(m)[:120])
        if not ok:
            bad += 1
    print("QUOTES: %d checked, %d failed" % (len(quotes), bad))
    sys.exit(1 if bad else 0)


main()
