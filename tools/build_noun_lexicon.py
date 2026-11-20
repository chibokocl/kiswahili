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

# Any dictionary entry start (noun, verb, adjective ...): used to find where a definition ends.
ANY_ENTRY = re.compile(
    r"(?m)^[^\s|()]+?\d{0,2}[ \t]+(?:Pia,[^\n]{0,40}?|\([^)\n]*\)[ \t]+)?\b(?:nm|kt|kv|kl|ki|kh|ku|kw)\b")

# --- animacy from the first sense of the definition (the definition itself is not stored) ---
ANIMATE_HEADS = set("""mtu watu binadamu mwanamume mwanamke mwanamme mnyama wanyama ndege samaki mdudu wadudu
nyoka mtoto watoto kijana msichana mvulana mzee kiumbe viumbe jini shetani malaika mja mtumishi kiongozi
mfalme malkia mtawala mganga mwalimu mwanafunzi askari mwanajeshi kuku mbwa paka nyuki mjusi chura nyani
ng'ombe mbuzi kondoo punda farasi ngamia simba chui tembo mwenyeji mgeni jirani rafiki adui mkulima
mfanyakazi mwanachama mkuu mwenye aliye anayefanya anayependa ambaye mwana mzazi mama baba ndugu mjomba
shangazi bibi babu mjukuu mpwa kabila jamaa""".split())
INANIMATE_HEADS = set("""hali sehemu tendo kitendo kipande chombo kifaa kipimo kazi eneo tabia mtindo jinsi mti
mmea tunda ugonjwa maradhi kitu vitu mchezo mkusanyiko upande herufi taaluma ala pahali mahali kiungo jumla
mchanganyiko mfumo uwezo elimu njia nguo chakula kinywaji siku wakati sauti harufu rangi mji nchi mto bahari
kitabu ufundi desturi utaratibu maneno neno tamko mashine vifaa madini kimiminika dawa chumba nyumba jengo
barabara kisiwa jambo hisia mawazo wazo tukio sherehe shughuli namna kipindi mwezi mwaka wiki hatua
ugumu uvimbe kidonda jeraha kelele fujo ghasia mali pesa fedha sarafu mapato gharama bei kodi ushuru
ardhi shamba mlima bonde pwani ziwa mvua upepo moto maji jua mwanga giza joto baridi hewa kemikali
mabaki ngozi nywele mfupa damu nyama maziwa mafuta sukari chumvi unga mkate""".split())


def _first_sense_words(body):
    body = re.sub(r"\s+", " ", body.strip())
    body = re.sub(r"^(\([a-z.]+\)\s*)+", "", body)            # (kd) (ksh) labels
    body = re.sub(r"^\d\.\s*", "", body)
    return [w.strip(".,;:()!?").lower() for w in body.split()[:6]]


def definition_head(body):
    w = _first_sense_words(body)
    if len(w) >= 3 and w[0] in ("aina", "namna", "jina") and w[1] in ("ya", "la", "wa"):
        return w[2]
    return w[0] if w else ""


def animacy(ngeli, body):
    """1 = animate, 0 = inanimate, None = unknown.  Class 1/2 nouns are animate by class."""
    if ngeli in ("1/2", "1a/2a"):
        return 1
    head = definition_head(body)
    if head in ANIMATE_HEADS:
        return 1
    if head in INANIMATE_HEADS:
        return 0
    return None



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
    starts = [m.start() for m in ANY_ENTRY.finditer(text)] + [len(text)]
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
        nxt = next((x for x in starts if x > m.end()), len(text))
        body = text[m.end():min(nxt, m.end() + 300)]
        anim = animacy(ngeli, body)
        heads = definition_head(body)
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
                # homographs: any animate sense wins; inanimate only if every sense agrees
                old = entries[key]["anim"]
                entries[key]["anim"] = 1 if 1 in (old, anim) else (0 if old == 0 and anim == 0 else None)
                continue
            entries[key] = {"w": word, "ngeli": ngeli, "n": number, "pl": plural,
                            "inv": invariable, "proper": proper, "variant": is_variant,
                            "anim": anim, "_head": heads}
            stats["entries"] += 1
    out = list(entries.values())
    # "aina ya kaa": inherit animacy from the entry for the head word
    by_word = {}
    for e in out:
        by_word.setdefault(e["w"], []).append(e["anim"])
    for _ in range(2):
        for e in out:
            if e["anim"] is None and e["_head"] in by_word:
                vals = by_word[e["_head"]]
                if 1 in vals:
                    e["anim"] = 1
                elif vals and all(v == 0 for v in vals):
                    e["anim"] = 0
        by_word = {}
        for e in out:
            by_word.setdefault(e["w"], []).append(e["anim"])
    for e in out:
        e.pop("_head", None)
    stats["animate"] = sum(1 for e in out if e["anim"] == 1)
    stats["inanimate"] = sum(1 for e in out if e["anim"] == 0)
    stats["animacy_unknown"] = sum(1 for e in out if e["anim"] is None)
    return out, stats


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
    cols = ["w", "ngeli", "n", "pl", "inv", "proper", "variant", "anim"]
    out = {
        "meta": {
            "source": "Kamusi Teule ya Kiswahili, 3rd ed. (EAEP). Headwords, ngeli, explicit "
                      "plurals and an animacy flag derived from each definition's opening words; "
                      "definitions are not stored.",
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
