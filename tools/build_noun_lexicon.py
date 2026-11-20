#!/usr/bin/env python3
"""
Build the noun lexicon (headword -> ngeli) from *Kamusi Teule ya Kiswahili*.

Entries in the dictionary look like::

    afisa nm (maafisa) |a-/wa-| mtu ambaye ...
    kitabu nm (vitabu) |ki-/vi-| ...

i.e. ``headword  nm  [(explicit plural)]  |singular-prefix/plural-prefix|  gloss``.
Only the headword, ngeli tag and explicit plural are kept -- not the definitions.

Usage:
    python tools/build_noun_lexicon.py swahili_corpus/kamusi.pdf \
        kiswahili_engine/data/noun_lexicon.json

Requires poppler's ``pdftotext`` on PATH.
"""

import argparse
import collections
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

# (singular agreement, plural agreement) -> (ngeli key used by the engine, number, invariable)
TAG_MAP = {
    ("a", "wa"): ("1/2", "singular", False),
    ("a", "a"): ("1/2", "singular", True),
    ("i", "zi"): ("9/10", "singular", False),
    ("i", "i"): ("9/10", "singular", True),
    ("u", "u"): ("14/6a", "singular", True),
    ("u", "ya"): ("14/6a", "singular", False),
    ("u", "i"): ("3/4", "singular", False),
    ("u", "zi"): ("11/10a", "singular", False),
    ("li", "ya"): ("5/6", "singular", False),
    ("li", "li"): ("5/6", "singular", True),
    ("ya", "ya"): ("5/6", "plural", True),      # maji, mafuta: ma- forms with no singular
    ("ki", "vi"): ("7/8", "singular", False),
    ("ki", "ki"): ("7/8", "singular", True),
    ("vi", "vi"): ("7/8", "plural", True),
    ("zi", "zi"): ("9/10", "plural", True),
    ("li",): ("5/6", "singular", True),
    ("i",): ("9/10", "singular", True),
    ("wa",): ("1/2", "plural", True),
    ("zi",): ("9/10", "plural", True),
    ("ya",): ("5/6", "plural", True),
    ("ku",): ("15", "singular", True),
    ("pa",): ("16", "singular", True),
    ("mu",): ("18", "singular", True),
    ("pa", "ku", "mu"): ("16", "singular", True),   # locative nouns (pahali ...)
}

ENTRY = re.compile(
    r"(?m)^(?P<head>[^\s|()]+?)(?P<hom>\d{1,2})?[ \t]+(?P<mid>[^|\n]{0,60}?)\bnm\b"
    r"(?P<post>[^|\n]{0,40}?)[ \t]*\n?[ \t]*(?:"
    r"\|(?P<t1>[^|()]{1,20})[|)]"                       # |a-/wa-|   (closing may be ')')
    r"|\((?P<t2>[a-z]{1,2}-?/[^|()]{1,15})[|)]"          # (a-/wa-|   (opening mangled)
    r"|(?P<t3>[a-z]{1,2}-/[a-z]{1,2}-?)\|"               # a-/wa-|    (opening missing)
    r")"
)
WORD = re.compile(r"^[a-z]+(?:['-][a-z]+)*$")


def normalise_tag(raw):
    """'|a-/wa-|', 'ki-vi-', 'li-/ya)' ... -> ('a','wa') etc.; None if unusable."""
    t = re.sub(r"\s+", "", raw.lower())
    parts = t.split("/") if "/" in t else [p for p in t.split("-") if p]
    parts = [p.strip("-") for p in parts]
    if not parts or parts[0] == "" or not all(re.fullmatch(r"[a-z]{1,2}", p) for p in parts):
        return None
    return tuple(parts)


def clean_word(w):
    w = w.replace("’", "'").replace("‘", "'").lower().strip(".,;:!?")
    return w if WORD.match(w) else None


def plural_from(text):
    """First word-like token inside an '(explicit plural)' group."""
    m = re.search(r"\(([^)]*)\)", text)
    if not m:
        return None
    for tok in re.split(r"[,\s]+", m.group(1)):
        w = clean_word(tok)
        if w and len(w) > 1:
            return w
    return None


def parse(text):
    text = text.replace("\x0c", "\n")
    stats = collections.Counter()
    entries = {}
    for m in ENTRY.finditer(text):
        stats["matched"] += 1
        mid = m.group("mid").strip()
        head = clean_word(m.group("head"))
        tag = normalise_tag(m.group("t1") or m.group("t2") or m.group("t3"))
        if not head:
            stats["skipped_headword"] += 1
            continue
        # multi-word headwords ("Agano la Kale"): mid holds the rest of the phrase
        if mid and not re.match(r"^(Pia,|\(|[a-z]+\s*$)", mid) and len(mid.split()) > 0 \
                and not mid.startswith("Pia,"):
            if not re.fullmatch(r"\(.*\)", mid):
                stats["skipped_phrase"] += 1
                continue
        if tag not in TAG_MAP:
            stats["skipped_tag"] += 1
            stats["tag:" + "/".join(tag or ("?",))] += 1
            continue
        ngeli, number, invariable = TAG_MAP[tag]
        plural = plural_from(mid) or plural_from(m.group("post"))
        proper = m.group("head")[:1].isupper()
        variants = []
        pm = re.match(r"Pia,\s*(.+)", mid)
        if pm:
            for tok in re.split(r"[,;]\s*", pm.group(1)):
                v = clean_word(tok.split("(")[0].strip())
                if v and v != head:
                    variants.append(v)
        for word, is_variant in [(head, False)] + [(v, True) for v in variants]:
            key = (word, ngeli, number)
            if key in entries:
                if plural and not entries[key]["pl"]:
                    entries[key]["pl"] = plural
                continue
            entries[key] = {"w": word, "ngeli": ngeli, "n": number, "pl": plural,
                            "inv": invariable, "proper": proper, "variant": is_variant}
            stats["entries"] += 1
    return list(entries.values()), stats


def extract_text(pdf):
    """Dictionary text in reading order (poppler's non-layout mode keeps columns apart)."""
    if not shutil.which("pdftotext"):
        sys.exit("pdftotext (poppler) is required")
    return subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True,
                          check=True).stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("out")
    args = ap.parse_args()
    text = extract_text(args.pdf)
    entries, stats = parse(text)
    entries.sort(key=lambda e: (e["w"], e["ngeli"]))
    cols = ["w", "ngeli", "n", "pl", "inv", "proper", "variant"]
    out = {
        "meta": {
            "source": "Kamusi Teule ya Kiswahili, 3rd ed. (EAEP). Headwords, ngeli and "
                      "explicit plurals only; definitions are not stored.",
            "generated": date.today().isoformat(),
            "columns": cols,
            "stats": {k: v for k, v in stats.items() if not k.startswith("tag:")},
            "unmapped_tags": {k[4:]: v for k, v in stats.items() if k.startswith("tag:")},
        },
        "entries": [[e[c] for c in cols] for e in entries],
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")),
                              encoding="utf-8")
    print(json.dumps(out["meta"]["stats"], indent=1))
    print("unmapped tags:", dict(sorted(out["meta"]["unmapped_tags"].items(),
                                         key=lambda kv: -kv[1])[:10]))


if __name__ == "__main__":
    main()
