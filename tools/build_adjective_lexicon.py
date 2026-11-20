#!/usr/bin/env python3
"""
Build the adjective lexicon from *Kamusi Teule ya Kiswahili* (``kv`` = kivumishi entries).

* ``-zuri kv ...``  hyphen-initial  -> an inflecting stem (mzuri, wazuri, kizuri ...)
* ``adimu kv ...``  no hyphen       -> an invariable adjective (adimu, aali ...)

Kamusi Teule is a school dictionary and omits many basic adjectives (-kubwa, -dogo,
-refu ...), so a short hand-curated core list is merged in and tagged ``curated``.

Usage:
    python tools/build_adjective_lexicon.py swahili_corpus/kamusi.pdf \
        kiswahili_engine/data/adjective_lexicon.json
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_noun_lexicon import extract_text  # noqa: E402

# kv entries that are not ordinary adjective stems (pronominal/special prefix systems)
NOT_ADJECTIVE_STEMS = {"enye", "enyewe", "pi", "po", "enu", "angu", "ake", "ao", "etu", "ako",
                       "a", "o", "ote", "elekezi", "enezi"}

# Basic adjectives and numerals missing from the dictionary (hand-curated).
CURATED = [
    "kubwa", "dogo", "refu", "fupi", "baya", "nene", "bichi", "bivu", "pana", "changa", "chungu",
    "moja", "wili", "tatu", "nne", "tano", "ngapi",
]

KV = re.compile(r"(?m)^(?P<head>-?[A-Za-z']+?)(?P<hom>\d{1,2})?[ \t]+(?:\([^)\n]*\)[ \t]+)?kv\b")


def parse(text):
    text = text.replace("\x0c", "\n").replace("’", "'")
    stems, invariable = {}, set()
    for m in KV.finditer(text):
        head = m.group("head")
        if head.startswith("-"):
            stem = head[1:].lower()
            if stem and stem not in NOT_ADJECTIVE_STEMS:
                stems[stem] = "kamusi"
        elif head.islower() and len(head) > 2:
            invariable.add(head)
    for s in CURATED:
        stems.setdefault(s, "curated")
    return stems, sorted(invariable - set(stems))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("out")
    a = ap.parse_args()
    stems, invariable = parse(extract_text(a.pdf))
    out = {
        "meta": {
            "source": "Kamusi Teule ya Kiswahili, 3rd ed. (EAEP) kv entries + a hand-curated core list. "
                      "Definitions are not stored.",
            "generated": date.today().isoformat(),
            "stems": len(stems), "invariable": len(invariable),
        },
        "stems": [[s, src] for s, src in sorted(stems.items())],
        "invariable": invariable,
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps(out["meta"], indent=1))


if __name__ == "__main__":
    main()
