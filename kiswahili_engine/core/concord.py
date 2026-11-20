"""
Noun-class concord for adjectives, possessives, the connective -a and -ote.

Two prefix systems are generated:

* **adjectival**  (mzuri, wazuri, kizuri, nzuri ...)  for the adjective lexicon stems
* **pronominal**  (wa/ya/cha ..., wangu/yangu/changu ..., wote/yote/chote ...)

Forms are generated for every stem and class, then *indexed by surface form*, so
recognising ``kizuri`` as "class 7 of -zuri" needs no inverse rules.  Generation can be
wrong for rare stems, so the checker only suggests a form that is also attested in the
corpus.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import json

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "adjective_lexicon.json"

CLASSES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "14", "15", "16", "17", "18"]
VOWELS = "aeiou"

# pronominal prefixes: -a (connective), possessives, -ote
PRON_PREFIX = {"1": "w", "2": "w", "3": "w", "4": "y", "5": "l", "6": "y", "7": "ch", "8": "vy",
               "9": "y", "10": "z", "11": "w", "14": "w", "15": "kw", "16": "p", "17": "kw", "18": "mw"}
PRON_STEMS = {"a": "connective", "angu": "possessive", "ako": "possessive", "ake": "possessive",
              "etu": "possessive", "enu": "possessive", "ao": "possessive", "ote": "quantifier"}

# 9/10: nasal-initial stems
_NASAL = {"b": "mb", "d": "nd", "g": "ng", "j": "nj", "l": "nd", "r": "nd", "v": "mb", "w": "mb", "z": "nz"}


def adjective_form(stem: str, cls: str) -> Optional[str]:
    """Adjectival concord form of ``stem`` (without hyphen) for noun class ``cls``."""
    s = stem
    v = s[0] in VOWELS
    c0 = s[0]
    if cls in ("1", "3", "11", "14"):
        return ("mw" + s) if v else ("m" + s)
    if cls == "2":
        if c0 == "e":
            return "w" + s
        if c0 == "i":
            return "we" + s[1:]
        return "wa" + s
    if cls == "4":
        if c0 == "e":
            return "my" + s
        if c0 == "i":
            return "m" + s                     # mingi, mingine
        return "mi" + s
    if cls == "5":
        if s == "pya":
            return "jipya"
        if s in ("moja",):
            return s
        return ("j" + s) if v else s
    if cls == "6":
        if c0 in "ei":
            return "me" + s[1:] if c0 == "i" else "m" + s
        return "ma" + s
    if cls == "7":
        if c0 == "e":
            return "ch" + s
        if c0 == "i":
            return "k" + s                     # kingi, kingine
        return "ki" + s
    if cls == "8":
        if c0 == "e":
            return "vy" + s
        if c0 == "i":
            return "v" + s                     # vingi, vingine
        return "vi" + s
    if cls in ("9", "10"):
        if s == "ema":
            return "njema"
        if s == "pya":
            return "mpya"
        if v:
            return "ny" + s
        if c0 in _NASAL:
            return _NASAL[c0] + s[1:]
        return s
    if cls in ("15", "17"):
        return ("kw" + s) if v else ("ku" + s)
    if cls == "16":
        return ("pe" + s[1:]) if c0 in "ei" else ("pa" + s)
    if cls == "18":
        return ("mw" + s) if v else ("mu" + s)
    return None


def pronominal_form(stem: str, cls: str) -> Optional[str]:
    p = PRON_PREFIX.get(cls)
    return (p + stem) if p else None


@dataclass(frozen=True)
class ConcordForm:
    word: str
    stem: str
    kind: str        # adjective | connective | possessive | quantifier
    cls: str


class ConcordLexicon:
    """Surface form -> (stem, kind, class) for every generated concord form."""

    def __init__(self, adjective_stems: List[str], invariable: Optional[List[str]] = None):
        self.stems = set(adjective_stems)
        self.invariable = set(invariable or ())
        self._index: Dict[str, List[ConcordForm]] = {}
        for stem in self.stems:
            for cls in CLASSES:
                f = adjective_form(stem, cls)
                if f:
                    self._add(ConcordForm(f, stem, "adjective", cls))
        for stem, kind in PRON_STEMS.items():
            for cls in CLASSES:
                self._add(ConcordForm(pronominal_form(stem, cls), stem, kind, cls))

    def _add(self, form: ConcordForm):
        bucket = self._index.setdefault(form.word, [])
        if form not in bucket:
            bucket.append(form)

    @classmethod
    def load(cls, path=None) -> "ConcordLexicon":
        d = json.loads(Path(path or DEFAULT_PATH).read_text(encoding="utf-8"))
        return cls([s for s, _ in d["stems"]], d.get("invariable"))

    def lookup(self, word: str) -> List[ConcordForm]:
        return list(self._index.get(word.lower().replace("’", "'"), []))

    def inflect(self, form: ConcordForm, cls: str) -> Optional[str]:
        if form.kind == "adjective":
            return adjective_form(form.stem, cls)
        return pronominal_form(form.stem, cls)

    def is_invariable(self, word: str) -> bool:
        return word.lower() in self.invariable

    def __contains__(self, word: str) -> bool:
        return bool(self.lookup(word)) or self.is_invariable(word)
