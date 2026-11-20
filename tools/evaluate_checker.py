#!/usr/bin/env python3
"""
Evaluate the Kiswahili checker the way a writing assistant is judged:

1. False alarms on clean text (issues per 1000 words) -- the number that decides whether
   anyone keeps the tool switched on.
2. Detection and fix accuracy on synthetic errors:
   * agreement: correct sentences built from the lexicons, then the subject marker corrupted
   * spelling : frequent words with one random edit

Synthetic sets are built from the same lexicons the checker uses, so they test the logic,
not real-world coverage.  Real learner/newsroom errors are the next gold set to collect.

    python tools/evaluate_checker.py [--n 500] [--seed 1]
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kiswahili_engine.checker import Checker, ADVERBIAL_NOUNS, tokenize  # noqa: E402
from kiswahili_engine.core.verb_morphology import subject_marker_for     # noqa: E402


def clean_text_false_alarms(chk, path):
    txt = Path(path).read_text(encoding="utf-8").split("===== Page 1 =====")[-1]
    txt = re.sub(r"[*#_|]", " ", txt)
    n_words = len(tokenize(txt))
    issues = chk.check(txt)
    by_rule = {}
    for i in issues:
        by_rule.setdefault(i.rule, []).append(i)
    print(f"\n== False alarms on clean text ({n_words} words, {Path(path).name}) ==")
    for rule, items in sorted(by_rule.items()):
        print(f"  {rule:7} {len(items):4d}  ({1000 * len(items) / n_words:.1f} per 1000 words)")
    if not issues:
        print("  none")
    for rule, items in by_rule.items():
        print(f"  {rule} examples:", [i.text for i in items[:12]])
    print("  note: azimio.text is also part of the spelling corpus, so SPELL is optimistic here.")


def agreement_eval(chk, n, rng):
    lex, vp = chk.ns.noun_lexicon, chk.ns.verb_parser
    nouns = []
    for key, entries in lex._index.items():
        e = entries[0]
        if (len(entries) == 1 and e.source == "headword" and e.number == "singular"
                and not e.proper and not e.variant and e.ngeli in
                {"1/2", "3/4", "5/6", "7/8", "9/10", "11/10a", "14/6a"}
                and key.isalpha() and len(key) > 3 and key not in ADVERBIAL_NOUNS
                and not key.endswith("ni") and key not in chk.known - set(lex._index)):
            nouns.append(e)
    roots = [r for r in vp.lexicon if r.isalpha() and 3 <= len(r) <= 7 and r[-1] not in "aeiou"
             and len(vp.verb_info.get(r, {}).get("exts", ())) >= 2]
    nouns.sort(key=lambda e: e.word)
    roots.sort()
    rng.shuffle(nouns)
    tams = ["me", "li", "na", "ta"]
    stats = dict(n=0, fp=0, detected=0, fixed_top1=0, missed_exempt=0)
    wrong_by_class = {"1/2": ["ki", "li", "u"], "default": ["wa", "a"]}
    for e in nouns[:n]:
        root, tam = rng.choice(roots), rng.choice(tams)
        good_sm = subject_marker_for(e.ngeli, "singular")
        if not good_sm:
            continue
        good = f"{good_sm}{tam}{root}a"
        sent = f"{e.word.capitalize()} {good} haraka."
        stats["n"] += 1
        if any(i.rule == "AGR-SV" for i in chk.check(sent)):
            stats["fp"] += 1
        # corrupt the marker with something that is wrong for this class and not exempt
        bad_pool = ["ki", "li", "u", "i", "vi", "zi", "pa"] if e.ngeli != "1/2" else ["ki", "li", "i", "zi"]
        bad_pool = [m for m in bad_pool if m != good_sm]
        bad_sm = rng.choice(bad_pool)
        bad = f"{bad_sm}{tam}{root}a"
        found = [i for i in chk.check(f"{e.word.capitalize()} {bad} haraka.") if i.rule == "AGR-SV"]
        if found:
            stats["detected"] += 1
            if found[0].suggestions and found[0].suggestions[0].text == good:
                stats["fixed_top1"] += 1
    n_ = max(stats["n"], 1)
    print(f"\n== Agreement (synthetic, {stats['n']} sentences) ==")
    print(f"  false alarms on correct sentences: {stats['fp']} ({stats['fp'] / n_:.1%})")
    print(f"  errors detected:                   {stats['detected']} ({stats['detected'] / n_:.1%})")
    print(f"  of detected, fix == original:      {stats['fixed_top1']} "
          f"({stats['fixed_top1'] / max(stats['detected'], 1):.1%})")


def concord_eval(chk, n, rng):
    """noun + adjective: correct agreement must stay silent, a wrong class must be caught."""
    from kiswahili_engine.core.concord import adjective_form
    lex = chk.ns.noun_lexicon
    stems = ["zuri", "kubwa", "dogo", "refu", "pya", "baya", "tamu", "gumu", "nene"]
    nouns = []
    for key, entries in lex._index.items():
        e = entries[0]
        if (len(entries) == 1 and e.source == "headword" and e.number == "singular" and not e.proper
                and e.ngeli in {"3/4", "7/8", "9/10", "5/6"} and key.isalpha() and len(key) > 3
                and key not in ADVERBIAL_NOUNS and not key.endswith("ni")
                and not chk.concord.lookup(key) and key in chk.known):
            nouns.append(e)
    nouns.sort(key=lambda e: e.word)
    rng.shuffle(nouns)
    cls_of = {"3/4": "3", "7/8": "7", "9/10": "9", "5/6": "5"}
    # wrong classes that no animate-noun exemption would forgive
    wrong_pool = {"3": ["7", "9", "5"], "7": ["4", "9", "6"], "9": ["7", "4", "6"], "5": ["7", "4", "9"]}
    st = dict(n=0, fp=0, detected=0, fixed=0)
    for e in nouns:
        if st["n"] >= n:
            break
        stem = rng.choice(stems)
        c = cls_of[e.ngeli]
        good, bad = adjective_form(stem, c), adjective_form(stem, rng.choice(wrong_pool[c]))
        if not good or not bad or good == bad or chk.freq.get(good, 0) < 2:
            continue
        st["n"] += 1
        w = e.word.capitalize()
        if any(i.rule == "AGR-NA" for i in chk.check(f"Nilimwona {e.word} {good} sana.")):
            st["fp"] += 1
        found = [i for i in chk.check(f"Nilimwona {e.word} {bad} sana.") if i.rule == "AGR-NA"]
        if found:
            st["detected"] += 1
            st["fixed"] += bool(found[0].suggestions and found[0].suggestions[0].text == good)
    n_ = max(st["n"], 1)
    print(f"\n== Noun-adjective concord (synthetic, {st['n']} phrases) ==")
    print(f"  false alarms on correct phrases: {st['fp']} ({st['fp'] / n_:.1%})")
    print(f"  errors detected:                 {st['detected']} ({st['detected'] / n_:.1%})")
    print(f"  of detected, fix == original:    {st['fixed']} ({st['fixed'] / max(st['detected'], 1):.1%})")


def typo(w, rng):
    kind = rng.choice(["del", "ins", "sub", "swap"])
    i = rng.randrange(1, len(w) - 1)
    if kind == "del":
        return w[:i] + w[i + 1:]
    if kind == "ins":
        return w[:i] + rng.choice("abcdefghijklmnoprstuwyz") + w[i:]
    if kind == "sub":
        return w[:i] + rng.choice("abcdefghijklmnoprstuwyz") + w[i + 1:]
    return w[:i] + w[i + 1] + w[i] + w[i + 2:] if w[i] != w[i + 1] else w


def spelling_eval(chk, n, rng):
    words = sorted(w for w, c in chk.freq.items() if c >= 20 and w.isalpha() and 5 <= len(w) <= 10
                   and w in chk.known)
    rng.shuffle(words)
    s = dict(n=0, fp=0, flagged=0, top1=0, top3=0, was_valid=0)
    for w in words[:n]:
        t = typo(w, rng)
        if t == w:
            continue
        s["n"] += 1
        if any(i.rule == "SPELL" and i.text == w for i in chk.check(f"Hii ni {w} sana.")):
            s["fp"] += 1
        if chk._is_known(t, t):                 # the edit produced another real word
            s["was_valid"] += 1
            continue
        found = [i for i in chk.check(f"Hii ni {t} sana.") if i.rule == "SPELL" and i.text == t]
        if found:
            s["flagged"] += 1
            sug = [x.text for x in found[0].suggestions]
            s["top1"] += bool(sug and sug[0] == w)
            s["top3"] += w in sug[:3]
    n_ = max(s["n"] - s["was_valid"], 1)
    print(f"\n== Spelling (synthetic single-edit typos, {s['n']} words) ==")
    print(f"  false alarms on the correct word:  {s['fp']} ({s['fp'] / max(s['n'], 1):.1%})")
    print(f"  edit happened to make a real word: {s['was_valid']} (excluded below)")
    print(f"  typos flagged:                     {s['flagged']} ({s['flagged'] / n_:.1%})")
    print(f"  correct word suggested top-1/top-3: {s['top1'] / n_:.1%} / {s['top3'] / n_:.1%} of typos")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    chk = Checker()
    clean_text_false_alarms(chk, ROOT / "swahili_corpus" / "azimio.text")
    agreement_eval(chk, a.n, rng)
    concord_eval(chk, a.n, rng)
    spelling_eval(chk, a.n, rng)


if __name__ == "__main__":
    main()
