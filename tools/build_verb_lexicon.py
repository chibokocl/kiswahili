#!/usr/bin/env python3
"""
Build the verb-root lexicon from *Kamusi Teule ya Kiswahili*.

Verb entries look like::

    end.a kt -ele- 1. toka pahali ...  (~ea, ~eka, ~esha, ~ewa)
    j.a2 kt -ele- sogea karibu ...
    jib.u2 kt -ele- itikia ...         (~ia, ~iwa)
    fotoa kt -ele- piga kitu picha     (no dot: root boundary not marked)

The dot marks the root/final-vowel boundary, ``-ele-``/``-sie-`` is transitive/
intransitive, and ``(~...)`` lists the derived extensions the dictionary attests.

Usage:
    python tools/build_verb_lexicon.py swahili_corpus/kamusi.pdf \
        kiswahili_engine/data/verb_lexicon.json
"""

import argparse
import collections
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_noun_lexicon import extract_text, ANY_ENTRY  # noqa: E402

VERB = re.compile(
    r"(?m)^(?P<head>[^\s|()]+?)(?P<hom>\d{1,2})?[ \t]+(?P<mid>(?:Pia,[^\n]{0,40}?|\([^)\n]*\))?)"
    r"[ \t]*\bkt\b[ \t]*(?P<tr>-(?:ele|sie)-(?:[ \t]*/[ \t]*-(?:ele|sie)-)?)?")
EXTS = re.compile(r"\(\s*(~[^)]{1,80})\)")
HEAD = re.compile(r"^(?P<root>[a-z']+)\.(?P<fv>[aeiu])$|^(?P<plain>[a-z']+)$")


def parse(text):
    text = text.replace("\x0c", "\n").replace("’", "'")
    starts = [m.start() for m in ANY_ENTRY.finditer(text)] + [len(text)]
    stats = collections.Counter()
    verbs = {}
    for m in VERB.finditer(text):
        stats["matched"] += 1
        head = m.group("head").lower()
        hm = HEAD.match(head)
        if not hm:
            stats["skipped_headword"] += 1
            continue
        if hm.group("root"):
            root, fv, dotted = hm.group("root"), hm.group("fv"), True
        else:
            w = hm.group("plain")
            if len(w) < 2:
                stats["skipped_headword"] += 1
                continue
            dotted = False
            root, fv = (w[:-1], "a") if w.endswith("a") else (w, "")
        # entry body: up to the next entry start (capped) -> attested extensions
        nxt = next((s for s in starts if s > m.end()), len(text))
        body = text[m.end():min(nxt, m.end() + 900)]
        exts = []
        em = EXTS.search(body)
        if em:
            exts = [t.strip().lstrip("~").lower() for t in re.split(r"[,\s]+", em.group(1))
                    if t.strip().lstrip("~")]
            exts = [e for e in exts if re.fullmatch(r"[a-z]+", e)]
        tr = (m.group("tr") or "").replace(" ", "")
        trans = sorted({t for t in ("ele", "sie") if t in tr})
        key = (root, fv)
        e = verbs.setdefault(key, {"root": root, "fv": fv, "dotted": dotted,
                                   "trans": set(), "exts": set(), "n": 0})
        e["dotted"] = e["dotted"] or dotted
        e["trans"].update(trans)
        e["exts"].update(exts)
        e["n"] += 1
        stats["entries"] += 1
    out = []
    for e in verbs.values():
        e["trans"] = sorted(e["trans"])
        e["exts"] = sorted(e["exts"])
        out.append(e)
    out.sort(key=lambda e: (e["root"], e["fv"]))
    stats["distinct_roots"] = len(out)
    stats["with_attested_extensions"] = sum(1 for e in out if e["exts"])
    stats["dotted"] = sum(1 for e in out if e["dotted"])
    return out, stats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("out")
    args = ap.parse_args()
    entries, stats = parse(extract_text(args.pdf))
    cols = ["root", "fv", "dotted", "trans", "exts"]
    out = {
        "meta": {
            "source": "Kamusi Teule ya Kiswahili, 3rd ed. (EAEP). Roots, final vowel, "
                      "transitivity and attested extensions only; definitions are not stored.",
            "generated": date.today().isoformat(),
            "columns": cols,
            "stats": dict(stats),
        },
        "entries": [[e[c] for c in cols] for e in entries],
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")),
                              encoding="utf-8")
    print(json.dumps(out["meta"]["stats"], indent=1))


if __name__ == "__main__":
    main()
