"""
Learn noun classes from running text -- no dictionary needed.

A noun's class shows in the words that agree with it.  In *kitabu cha mtoto* the connective
*cha* can only agree with a class 7 noun; *kizuri*, *changu* and *hiki* point the same way, and
so does the subject marker of the verb in *kitabu kimeanguka*.  Counting those agreeing words
after every word in a corpus gives each word a probability for each class, so new vocabulary
(*kituo*, *simu*) is classified as soon as it appears in text.

    python -m kiswahili_engine.learn corpus.txt other.pdf -o learned_noun_classes.json

Inputs may be plain UTF-8 text (preferred) or PDFs (read with poppler's ``pdftotext``).
The result is a small JSON file loaded by :class:`~kiswahili_engine.core.noun_lexicon.NounLexicon`
as a fallback for words the dictionary lacks.  Quality depends on the text: use well-edited,
modern prose, because whatever the corpus treats as correct becomes correct.
"""

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import argparse
import json
import re
import shutil
import subprocess
import sys

from .core.concord import ConcordLexicon, CLASSES
from .core.verb_morphology import VerbParser, VERB_THRESHOLD

DEFAULT_OUT = Path(__file__).resolve().parent / "data" / "learned_noun_classes.json"

# Demonstratives that follow their noun ("kitabu hiki"), with the classes they agree with.
DEMONSTRATIVES = {
    "huyu": {"1"}, "huyo": {"1"}, "yule": {"1"},
    "hawa": {"2"}, "hao": {"2"}, "wale": {"2"},
    "huu": {"3", "11", "14"}, "huo": {"3", "11", "14"}, "ule": {"3", "11", "14"},
    "hii": {"4", "9"}, "hiyo": {"4", "9"}, "ile": {"4", "9"},
    "hili": {"5"}, "hilo": {"5"}, "lile": {"5"},
    "haya": {"6"}, "hayo": {"6"}, "yale": {"6"},
    "hiki": {"7"}, "hicho": {"7"}, "kile": {"7"},
    "hivi": {"8"}, "hivyo": {"8"}, "vile": {"8"},
    "hizi": {"10"}, "hizo": {"10"}, "zile": {"10"},
}

# Words that take 'ya'/'wa' after them but are not nouns (prepositions/adverbs/etc.).
NOT_NOUNS = set("""kabla baada juu chini mbele nyuma ndani nje karibu mbali badala pamoja miongoni
katikati kando hadi kwa na ni si hata kama lakini bali ili kwamba ambaye ambao ambayo ambazo
wote yote zote vyote lote chote kote pote mote yeye wao sisi mimi wewe nyinyi huyu hawa hii hizi
hili haya hiki hivi huu pia tena sasa leo jana kesho""".split())

LOCATIVE_FORMS = {"kwa", "pa", "mwa"}      # usually prepositions: no class evidence

WORD = re.compile(r"[a-z]+(?:'[a-z]+)*")
BOUNDARY = re.compile(r"[.,;:!?\"“”‘()\[\]\d—–/]+|\n\s*\n")


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        if not shutil.which("pdftotext"):
            sys.exit("pdftotext (poppler) is required to read PDFs")
        return subprocess.run(["pdftotext", str(path), "-"], capture_output=True, text=True,
                              check=True).stdout
    return path.read_text(encoding="utf-8", errors="ignore")


def clauses(text: str) -> Iterable[List[str]]:
    """Lower-cased word lists split at punctuation, digits and verse numbers (no adjacency across)."""
    text = text.lower().replace("’", "'")
    for piece in BOUNDARY.split(text):
        words = WORD.findall(piece)
        if len(words) > 1:
            yield words


def concord_classes(concord: ConcordLexicon) -> Dict[str, frozenset]:
    """Surface form -> the classes it agrees with, for every form that can signal a class."""
    table: Dict[str, set] = defaultdict(set)
    for form, entries in concord._index.items():
        if form in LOCATIVE_FORMS:
            continue
        for e in entries:
            table[form].add(e.cls)
    for w, classes in DEMONSTRATIVES.items():
        table[w] |= classes
    return {w: frozenset(c) for w, c in table.items()}


# Singular/plural class of each ngeli pair (the engine's keys)
PAIRS = {"1/2": ("1", "2"), "3/4": ("3", "4"), "5/6": ("5", "6"), "7/8": ("7", "8"),
         "9/10": ("9", "10"), "11/10a": ("11", "10"), "14/6a": ("14", "6")}
EPS = 0.02            # smoothing for forms a class never showed


def collect_forms(texts: Iterable[str], parser: Optional[VerbParser] = None,
                  verb_weight: float = 0.5):
    """For every word, count the agreeing forms that follow it: ``form -> weight``.

    Concord words (ya, cha, kizuri, changu, hiki ...) count 1; the subject marker of a tensed
    verb right after the word counts ``verb_weight`` (the word may not be its subject)."""
    concord = ConcordLexicon.load()
    signals = concord_classes(concord)
    parser = parser or VerbParser.from_kamusi()
    forms: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    verb_cache: Dict[str, Optional[str]] = {}
    verb_sig: Dict[str, frozenset] = {}

    def verb_signal(w: str) -> Optional[str]:
        if w not in verb_cache:
            p = parser.best(w)
            ok = bool(p and p.form == "finite" and p.score >= VERB_THRESHOLD
                      and (p.tam or p.polarity == "negative"))
            labels = frozenset(l for l in p.subject_labels if l in CLASSES) if ok else frozenset()
            key = None
            if labels:
                key = "SM:" + (p.negative_prefix or p.subject_marker)
                verb_sig[key] = labels
            verb_cache[w] = key
        return verb_cache[w]

    for text in texts:
        for words in clauses(text):
            for w1, w2 in zip(words, words[1:]):
                if w1 in NOT_NOUNS or w1 in signals or len(w1) < 3:
                    continue
                if w2 in signals:
                    forms[w1][w2] += 1.0
                else:
                    key = verb_signal(w2)
                    if key:
                        forms[w1][key] += verb_weight
    signals = dict(signals)
    signals.update(verb_sig)
    return forms, signals


def _emissions(signals: Dict[str, frozenset]) -> Dict[str, Dict[str, float]]:
    """P(form | class): uniform over the forms that can agree with the class."""
    members: Dict[str, List[str]] = defaultdict(list)
    for f, classes in signals.items():
        for c in classes:
            members[c].append(f)
    return {c: {f: 1.0 / len(fs) for f in fs} for c, fs in members.items()}


def build_model(forms, signals, min_obs: int = 3, min_support: float = 0.85, max_pairs: int = 3) -> Dict:
    """Which ngeli pairs are *consistent* with the agreeing forms seen after each word.

    A pair is consistent when at least ``min_support`` of the observations could agree with
    its singular or plural class (the rest is allowed as noise).  Nouns of classes 1, 3, 11 and
    14 share every singular connective and adjective form, so a noun seen only in the
    singular legitimately keeps several pairs; consumers should accept a modifier that fits
    *any* of them and flag only what fits *none*.  Pairs are ordered by a naive Bayes score
    (likelihood averaged over the pair's two classes, counts tempered by sqrt) so that
    ``mji + ya + za`` prefers a pair that explains both.
    """
    import math
    emit = _emissions(signals)
    model: Dict[str, List] = {}
    for w, fc in forms.items():
        total = sum(fc.values())
        if total < min_obs:
            continue
        scored = []
        for pair, (sg, pl) in PAIRS.items():
            fits = sum(c for f, c in fc.items() if {sg, pl} & signals.get(f, frozenset()))
            support = fits / total
            if support < min_support:
                continue
            ll = 0.0
            for f, cnt in fc.items():
                p = 0.5 * emit.get(sg, {}).get(f, 0.0) + 0.5 * emit.get(pl, {}).get(f, 0.0)
                ll += math.sqrt(cnt) * math.log(p + EPS)
            sg_w = sum(c for f, c in fc.items() if sg in signals.get(f, ()))
            pl_w = sum(c for f, c in fc.items() if pl in signals.get(f, ()))
            number = "s" if sg_w and not pl_w else "p" if pl_w and not sg_w else "sp"
            scored.append((ll, pair, round(support, 3), number))
        if not scored:
            continue                       # contradictory evidence: say nothing
        scored.sort(reverse=True)
        model[w] = [round(total, 1), [[pair, sup, num] for _, pair, sup, num in scored[:max_pairs]]]
    return model


def learn(paths: Iterable[Path], min_obs: int = 3, source_note: str = "") -> Dict:
    texts = [read_text(Path(p)) for p in paths]
    forms, signals = collect_forms(texts)
    return {
        "meta": {"inputs": [Path(p).name for p in paths], "min_obs": min_obs, "words": 0,
                 "source_note": source_note,
                 "format": "word -> [observations, [[ngeli pair, probability, number(s|p|sp)], ...]]"},
        "words": build_model(forms, signals, min_obs),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="text or PDF files")
    ap.add_argument("-o", "--out", default=str(DEFAULT_OUT))
    ap.add_argument("--min-obs", type=int, default=3)
    ap.add_argument("--source-note", default="", help="licence/attribution text stored in the output")
    a = ap.parse_args(argv)
    model = learn(a.inputs, a.min_obs, a.source_note)
    model["meta"]["words"] = len(model["words"])
    Path(a.out).write_text(json.dumps(model, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"learned classes for {len(model['words'])} words -> {a.out}")


if __name__ == "__main__":
    main()
