#!/usr/bin/env python3
"""
How well do classes learned from text agree with the dictionary?

Reads a learned-classes file (default: the packaged one) and, for every word that is also a
dictionary noun, checks whether the dictionary's ngeli pair is among the learner's candidates.
This is a sanity check of the learner, not training: the dictionary is never used to learn.

    python tools/evaluate_learner.py [learned.json]
"""

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
learned = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "kiswahili_engine" / "data" / "learned_noun_classes.json"
model = json.loads(learned.read_text(encoding="utf-8"))["words"]
d = json.loads((ROOT / "kiswahili_engine" / "data" / "noun_lexicon.json").read_text(encoding="utf-8"))
cols = d["meta"]["columns"]
gold = collections.defaultdict(set)
for row in d["entries"]:
    e = dict(zip(cols, row))
    if not e["proper"]:
        gold[e["w"]].add({"1a/2a": "1/2"}.get(e["ngeli"], e["ngeli"]))

known = [w for w in model if w in gold]
print(f"{len(model)} learned words; {len(known)} also in the dictionary; "
      f"{len(model) - len(known)} are new vocabulary")
print("observations | words | dictionary pair among candidates | single-candidate words")
for lo, hi in [(3, 10), (10, 30), (30, 100), (100, 10 ** 9)]:
    sel = [w for w in known if lo <= model[w][0] < hi]
    if not sel:
        continue
    hit = sum(any(p in gold[w] for p, _, _ in model[w][1]) for w in sel)
    one = [w for w in sel if len(model[w][1]) == 1]
    ok = sum(model[w][1][0][0] in gold[w] for w in one)
    print(f"{lo:>6}-{'' if hi > 10 ** 8 else hi:<6} | {len(sel):5d} | {hit / len(sel):6.1%} | "
          f"{len(one):4d} ({ok / max(len(one), 1):.0%} correct)")
allone = [w for w in known if len(model[w][1]) == 1]
print(f"overall: candidates contain the dictionary pair for "
      f"{sum(any(p in gold[w] for p, _, _ in model[w][1]) for w in known) / len(known):.1%}; "
      f"avg {sum(len(model[w][1]) for w in known) / len(known):.1f} candidates per word")
