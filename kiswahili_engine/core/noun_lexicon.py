"""
Noun lexicon: surface form -> ngeli, built from *Kamusi Teule ya Kiswahili*.

The data file ``data/noun_lexicon.json`` is produced by
``tools/build_noun_lexicon.py``.  It holds headwords, ngeli and explicit plurals.
Prefix heuristics cannot tell ``mtoto`` (1/2) from ``mti`` (3/4) or ``chakula``
(7/8) from a 9/10 noun, so the engine consults this lexicon first.

Lookup covers:

* the headword itself           (``mtoto``  -> 1/2 singular)
* explicit plurals in the book  (``watoto`` -> 1/2 plural)
* regular derived plurals       (``vitabu`` from ``kitabu``; lower confidence)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import json
import re

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "noun_lexicon.json"

# Confidence by evidence type
SOURCE_CONFIDENCE = {"headword": 0.95, "plural": 0.9, "plural_rule": 0.7}

# Singular word shapes typical for each ngeli: used only to rank *ambiguous* entries
_SHAPE = {
    "7/8": re.compile(r"^(ki|ch|ky)"),
    "3/4": re.compile(r"^(m|mw|mu)"),
    "1/2": re.compile(r"^(m|mw|mu)"),
    "5/6": re.compile(r"^(j|ji)"),
    "14/6a": re.compile(r"^(u|w)"),
    "11/10a": re.compile(r"^u"),
}


@dataclass(frozen=True)
class NounEntry:
    word: str                 # the surface form that was looked up
    lemma: str                # singular dictionary headword
    ngeli: str                # key used by NGELI_CLASSES ("1/2", "7/8", ...)
    number: str               # "singular" | "plural" (for this surface form)
    source: str               # headword | plural | plural_rule
    plural: Optional[str] = None
    invariable: bool = False
    proper: bool = False
    variant: bool = False

    @property
    def confidence(self) -> float:
        return SOURCE_CONFIDENCE[self.source]


def _derive_plural(word: str, ngeli: str) -> Optional[str]:
    """Regular plural for productive classes; None when it can't be derived safely."""
    if ngeli == "1/2":
        m = re.match(r"^mw([aeiou].*)", word)
        if m:
            return "w" + m.group(1)
        m = re.match(r"^m[u]?([^aeiou].*)", word)
        return "wa" + m.group(1) if m else None
    if ngeli == "3/4":
        m = re.match(r"^mw([aeiou].*)", word)
        if m:
            return "mi" + m.group(1)
        m = re.match(r"^m[u]?([^aeiou].*)", word)
        return "mi" + m.group(1) if m else None
    if ngeli == "7/8":
        if word.startswith("ki"):
            return "vi" + word[2:]
        if word.startswith("ch"):
            return "vy" + word[2:]
    if ngeli == "5/6" and not word.startswith("ma"):
        return "ma" + (word[2:] if word.startswith("ji") else word)
    return None


class NounLexicon:
    """Ranked lookup of noun forms.  Build with :meth:`load` or from raw entries."""

    def __init__(self, entries: Iterable[Dict]):
        self._index: Dict[str, List[NounEntry]] = {}
        self._headwords = 0
        for e in entries:
            self._add(e)

    # ---------------------------------------------------------- construction
    @classmethod
    def load(cls, path: Optional[str] = None) -> "NounLexicon":
        data = json.loads(Path(path or DEFAULT_PATH).read_text(encoding="utf-8"))
        cols = data["meta"]["columns"]
        return cls(dict(zip(cols, row)) for row in data["entries"])

    def _put(self, form: str, entry: NounEntry):
        bucket = self._index.setdefault(form, [])
        if not any(x.lemma == entry.lemma and x.ngeli == entry.ngeli
                   and x.number == entry.number for x in bucket):
            bucket.append(entry)

    def _add(self, e: Dict):
        word, ngeli, number = e["w"], e["ngeli"], e["n"]
        common = dict(lemma=word, ngeli=ngeli, plural=e.get("pl"),
                      invariable=bool(e.get("inv")), proper=bool(e.get("proper")),
                      variant=bool(e.get("variant")))
        self._put(word, NounEntry(word=word, number=number, source="headword", **common))
        self._headwords += 1
        if number != "singular":
            if ngeli == "9/10" and number == "plural":
                # plural-only listing (fedha: zi-) still takes singular agreement too
                self._put(word, NounEntry(word=word, number="singular", source="plural_rule", **common))
            return
        plural = e.get("pl")
        if ngeli == "9/10" and not plural:
            # most 9/10 nouns have an identical plural (dalili, sehemu: "dalili zimeanza")
            self._put(word, NounEntry(word=word, number="plural", source="plural_rule", **common))
        if plural:
            self._put(plural, NounEntry(word=plural, number="plural", source="plural", **common))
        elif not e.get("inv"):
            derived = _derive_plural(word, ngeli)
            if derived and derived != word:
                self._put(derived, NounEntry(word=derived, number="plural",
                                             source="plural_rule", **common))

    # ---------------------------------------------------------- lookup
    def lookup(self, word: str) -> List[NounEntry]:
        """All analyses of ``word``, best first.  Empty list if unknown."""
        w = word.lower().replace("’", "'").strip()
        found = self._index.get(w, [])
        if len(found) < 2:
            return list(found)
        order = {id(x): i for i, x in enumerate(found)}

        def rank(x: NounEntry):
            shape = _SHAPE.get(x.ngeli)
            fits = bool(shape and x.number == "singular" and shape.match(x.word))
            return (-x.confidence, x.variant, not fits, order[id(x)])
        return sorted(found, key=rank)

    def best(self, word: str) -> Optional[NounEntry]:
        found = self.lookup(word)
        return found[0] if found else None

    def candidates(self, word: str) -> List[Tuple[str, str]]:
        """(ngeli, number) pairs for ``word``, best first, duplicates removed."""
        seen, out = set(), []
        for e in self.lookup(word):
            if (e.ngeli, e.number) not in seen:
                seen.add((e.ngeli, e.number))
                out.append((e.ngeli, e.number))
        return out

    def __contains__(self, word: str) -> bool:
        return bool(self.lookup(word))

    def __len__(self) -> int:
        return self._headwords
