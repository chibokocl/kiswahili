"""
Slot-based Kiswahili verb parser.

Parses a surface verb into its morphemes::

    [NEG] SM [NEG2] [TAM] [REL] [OM] [ku] ROOT [EXT...] FV [REL-suffix]

Because Kiswahili verbs are ambiguous without a lexicon (is ``pikia`` the root
``pikia`` or ``pik`` + applicative?), the parser returns *every* plausible
analysis ranked by score.  Supplying a root lexicon (see
:meth:`VerbParser.from_wordlist`) sharpens the ranking.

Not covered: reversive/positional/reduplicated extensions, ``-ile`` perfect,
``amba-`` relatives, and vowel coalescence between a subject marker and a
vowel-initial root without TAM (e.g. ``aenda``).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple
import json
import re

from ..data.verb_data import (
    CLASS_TO_NGELI, SUBJECT_MARKERS, NEG_SUBJECT_MARKERS, PERSON_LABELS,
    OBJECT_MARKERS, TAM_POSITIVE, TAM_NEGATIVE, RELATIVE_MARKERS,
    RELATIVE_SUFFIXES, EXTENSIONS,
)

VOWELS = "aeiou"
DEFAULT_LEXICON_PATH = Path(__file__).resolve().parent.parent / "data" / "verb_lexicon.json"
MAX_EXTENSIONS = 3

# Score at or above which a finite parse is treated as "this is a verb"
VERB_THRESHOLD = 0.7


@dataclass
class VerbParse:
    """One candidate analysis of a verb form."""
    word: str
    form: str                                  # finite | infinitive | imperative
    polarity: str = "positive"
    negative_prefix: Optional[str] = None      # ha-, si-, hu- ... (portmanteau SM)
    subject_marker: Optional[str] = None
    subject_labels: List[str] = field(default_factory=list)
    tam: Optional[str] = None                  # surface TAM marker ("na", "li", ...)
    tam_name: Optional[str] = None
    relative: Optional[str] = None
    object_marker: Optional[str] = None
    object_labels: List[str] = field(default_factory=list)
    ku: Optional[str] = None                   # infinitive ku-/kw- or monosyllabic ku-
    root: str = ""
    extensions: List[Tuple[str, str]] = field(default_factory=list)  # (label, surface)
    final_vowel: str = ""
    relative_suffix: Optional[str] = None
    arabic_root: bool = False
    score: float = 0.0

    # ----------------------------------------------------------- views
    def morphemes(self) -> List[Tuple[str, str]]:
        """Ordered (surface, gloss) pairs."""
        out: List[Tuple[str, str]] = []
        if self.negative_prefix:
            out.append((self.negative_prefix, "NEG+SM " + "/".join(self.subject_labels)))
        elif self.subject_marker:
            out.append((self.subject_marker, "SM " + "/".join(self.subject_labels)))
        if self.tam:
            out.append((self.tam, self.tam_name or "TAM"))
        if self.relative:
            out.append((self.relative, "REL"))
        if self.object_marker:
            out.append((self.object_marker, "OM " + "/".join(self.object_labels)))
        if self.ku and self.form == "infinitive":
            out.insert(0, (self.ku, "INF"))
        elif self.ku:
            out.append((self.ku, "ku (monosyllabic)"))
        out.append((self.root, "ROOT"))
        for label, surface in self.extensions:
            out.append((surface, label.upper()[:4]))
        if self.final_vowel:
            out.append((self.final_vowel, "FV"))
        if self.relative_suffix:
            out.append((self.relative_suffix, "REL"))
        return [(s, g) for s, g in out if s]

    def segmentation(self) -> str:
        return "-".join(s for s, _ in self.morphemes())

    def subject_ngeli(self) -> List[Tuple[str, str]]:
        """(ngeli key, number) pairs the subject marker is compatible with."""
        out: List[Tuple[str, str]] = []
        for label in self.subject_labels:
            out.extend(CLASS_TO_NGELI.get(label, []))
        return out

    def retarget_subject(self, ngeli: str, number: str) -> Optional[str]:
        """The same verb with its subject marker changed to agree with (ngeli, number)."""
        old = self.negative_prefix or self.subject_marker
        new = subject_marker_for(ngeli, number, self.polarity == "negative")
        if not old or not new or not self.word.startswith(old):
            return None
        return new + self.word[len(old):]

    def to_dict(self) -> Dict:
        return {
            "word": self.word, "form": self.form, "polarity": self.polarity,
            "segmentation": self.segmentation(),
            "subject_marker": self.negative_prefix or self.subject_marker,
            "subject_labels": self.subject_labels,
            "tam": self.tam, "tense": self.tam_name, "relative": self.relative,
            "object_marker": self.object_marker, "root": self.root,
            "extensions": [e for e in self.extensions],
            "final_vowel": self.final_vowel, "score": round(self.score, 3),
        }


# --------------------------------------------------------------------- generation
def subject_marker_for(ngeli: str, number: str, negative: bool = False) -> Optional[str]:
    """Subject marker a verb needs to agree with a noun of (ngeli, number)."""
    table = NEG_SUBJECT_MARKERS if negative else SUBJECT_MARKERS
    for cls, readings in CLASS_TO_NGELI.items():
        if (ngeli, number) in readings:
            for marker, labels in table.items():
                if cls in labels:
                    return marker
    return None


# --------------------------------------------------------------------- helpers
def _has_vowel(s: str) -> bool:
    return any(c in VOWELS for c in s)


def _last_vowel(s: str) -> Optional[str]:
    for c in reversed(s):
        if c in VOWELS:
            return c
    return None


class VerbParser:
    """Enumerates and ranks verb analyses.  ``lexicon`` is an optional set of roots."""

    def __init__(self, lexicon: Optional[Iterable[str]] = None,
                 verb_info: Optional[Dict[str, Dict]] = None):
        self.lexicon: Set[str] = set(lexicon or ())
        # root -> {"trans": [...], "exts": {...attested extension endings...}}
        self.verb_info: Dict[str, Dict] = verb_info or {}
        self._sm = sorted(SUBJECT_MARKERS, key=len, reverse=True)
        self._nsm = sorted(NEG_SUBJECT_MARKERS, key=len, reverse=True)
        self._cache: Dict[str, List[VerbParse]] = {}

    # ------------------------------------------------------------ lexicon
    @classmethod
    def from_kamusi(cls, path=None) -> "VerbParser":
        """Parser backed by the dictionary-derived verb-root lexicon (``data/verb_lexicon.json``)."""
        data = json.loads(Path(path or DEFAULT_LEXICON_PATH).read_text(encoding="utf-8"))
        cols = data["meta"]["columns"]
        roots: Set[str] = set()
        info: Dict[str, Dict] = {}
        for row in data["entries"]:
            e = dict(zip(cols, row))
            root, fv = e["root"], e["fv"]
            roots.add(root)
            if fv in ("i", "u", "e"):
                roots.add(root + fv)          # Arabic-origin verbs keep their vowel (jibu)
            rec = info.setdefault(root, {"trans": set(), "exts": set()})
            rec["trans"].update(e["trans"])
            rec["exts"].update(e["exts"])
        return cls(roots, info)

    def is_known_root(self, root: str) -> bool:
        return root in self.lexicon

    @classmethod
    def from_wordlist(cls, path, min_count: int = 1) -> "VerbParser":
        """Build a root lexicon from infinitives (``ku``/``kw`` + root + ``a``) in a word list."""
        roots: Dict[str, int] = {}
        for line in Path(path).read_text(encoding="utf-8").split():
            w = line.strip().lower()
            if len(w) < 4 or not w.endswith("a") or not w.isalpha():
                continue
            if w.startswith("ku"):
                root = w[2:-1]
            elif w.startswith("kw") and w[2] in VOWELS:
                root = w[2:-1]
            else:
                continue
            if root:
                roots[root] = roots.get(root, 0) + 1
        # Infinitives with an object marker (kumwona) are not roots: drop OM+known-root forms.
        known = {r for r, n in roots.items() if n >= min_count}
        for r in list(known):
            for om in OBJECT_MARKERS:
                if r.startswith(om) and len(r) - len(om) >= 2 and r[len(om):] in known:
                    known.discard(r)
                    break
        return cls(known)

    # ------------------------------------------------------------ public API
    def parse(self, word: str) -> List[VerbParse]:
        """All plausible analyses of ``word``, best first."""
        w = re.sub(r"[^a-z']", "", word.lower())
        if not w:
            return []
        if w in self._cache:
            return self._cache[w]
        results: List[VerbParse] = []
        results += self._parse_infinitive(w)
        results += self._parse_finite(w)
        results += self._parse_imperative(w)
        seen, unique = set(), []
        for p in sorted(results, key=lambda p: (-p.score, len(p.extensions))):
            key = p.segmentation() + "|" + p.form + "|" + p.polarity
            if key not in seen:
                seen.add(key)
                unique.append(p)
        self._cache[w] = unique
        return unique

    def best(self, word: str, subject: Optional[Tuple[str, str]] = None) -> Optional[VerbParse]:
        """Best analysis.  ``subject`` = (ngeli key, number) prefers agreeing parses."""
        parses = self.parse(word)
        if not parses:
            return None
        if subject:
            agreeing = [p for p in parses if subject in p.subject_ngeli()]
            if agreeing and agreeing[0].score >= parses[0].score - 0.25:
                return agreeing[0]
        return parses[0]

    def is_finite_verb(self, word: str) -> bool:
        """True for confident finite parses.  Bare subjunctives (``mkate``) need
        sentence context, so TAM-less forms without a relative suffix don't count."""
        p = self.best(word)
        return bool(p and p.form == "finite" and p.score >= VERB_THRESHOLD
                    and (p.tam or p.relative_suffix))

    # ------------------------------------------------------------ finite verbs
    def _parse_finite(self, w: str) -> List[VerbParse]:
        out: List[VerbParse] = []

        # positive: SM [TAM] ...
        for sm in self._sm:
            if not w.startswith(sm):
                continue
            rest = w[len(sm):]
            for tam in list(TAM_POSITIVE) + ["", "si"]:
                if tam == "hu" or not rest.startswith(tam):
                    continue
                name = TAM_POSITIVE[tam][0] if tam in TAM_POSITIVE else (
                    "negative subjunctive" if tam == "si" else None)
                self._after_tam(out, w, rest[len(tam):], dict(
                    form="finite", polarity="positive", subject_marker=sm,
                    subject_labels=SUBJECT_MARKERS[sm], tam=tam or None, tam_name=name),
                    tam, allow_rel=bool(tam), allow_rel_suffix=(tam == ""))

        # habitual hu- (no subject marker)
        if w.startswith("hu"):
            self._after_tam(out, w, w[2:], dict(
                form="finite", polarity="positive", tam="hu", tam_name="habitual"),
                "hu", allow_rel=False, allow_rel_suffix=False)

        # negative: NEGSM [TAM]
        for nsm in self._nsm:
            if not w.startswith(nsm):
                continue
            rest = w[len(nsm):]
            for tam, (name, _) in TAM_NEGATIVE.items():
                if not rest.startswith(tam):
                    continue
                self._after_tam(out, w, rest[len(tam):], dict(
                    form="finite", polarity="negative", negative_prefix=nsm,
                    subject_labels=NEG_SUBJECT_MARKERS[nsm], tam=tam or None,
                    tam_name=name), "neg" + tam, allow_rel=False, allow_rel_suffix=False)
        return out

    def _after_tam(self, out, word, rest, base, tam_key, allow_rel, allow_rel_suffix):
        """Consume [REL] [OM] [ku] and then the stem."""
        rel_options = [(None, rest)]
        if allow_rel:
            rel_options += [(r, rest[len(r):]) for r in RELATIVE_MARKERS if rest.startswith(r)]

        for rel, r1 in rel_options:
            om_options = [(None, r1)]
            for om in OBJECT_MARKERS:
                if not r1.startswith(om) or len(r1) <= len(om):
                    continue
                nxt = r1[len(om)]
                if om == "mw" and nxt not in VOWELS:
                    continue
                if om == "m" and nxt in VOWELS:
                    continue
                om_options.append((om, r1[len(om):]))

            for om, r2 in om_options:
                ku_options = [(None, r2)]
                if om is None and r2.startswith("ku") and tam_key not in ("hu", "si"):
                    ku_options.append(("ku", r2[2:]))
                for ku, r3 in ku_options:
                    if not r3:
                        continue
                    self._finish(out, word, r3, dict(
                        base, relative=rel, object_marker=om,
                        object_labels=OBJECT_MARKERS.get(om, []), ku=ku),
                        tam_key, allow_rel_suffix)

    def _finish(self, out, word, rest, base, tam_key, allow_rel_suffix):
        """Resolve FV / extensions / relative suffix and score."""
        tam = base.get("tam")
        # which final vowels this TAM licenses
        if tam_key.startswith("neg"):
            kinds = {"i"} if tam_key == "neg" else {"a"}
        elif tam_key == "":
            kinds = {"a", "e"}
        elif tam_key == "si":
            kinds = {"a"} if base.get("relative") else {"e"}
        else:
            kinds = {"a"}

        suffix_options = [(None, rest)]
        if allow_rel_suffix:
            for s in RELATIVE_SUFFIXES:
                if rest.endswith(s) and len(rest) > len(s) + 1:
                    suffix_options.append((s, rest[:-len(s)]))

        for suffix, body in suffix_options:
            kinds_here = {"a"} & kinds if suffix else kinds
            for root, exts, fv, arabic in self._stems(body, kinds_here):
                if not self._plausible(root, exts, base["ku"], base["polarity"], tam_key):
                    continue
                p = VerbParse(word=word, root=root, extensions=exts, final_vowel=fv,
                              relative_suffix=suffix, arabic_root=arabic, **base)
                if tam_key == "" and fv == "e":
                    p.tam_name = "subjunctive"
                elif tam_key == "":
                    p.tam_name = "general present"
                p.score = self._score(p, tam_key)
                if p.score > 0:
                    out.append(p)

    # ------------------------------------------------------------ infinitive
    def _parse_infinitive(self, w: str) -> List[VerbParse]:
        out: List[VerbParse] = []
        for ku in ("ku", "kw"):
            if not w.startswith(ku):
                continue
            rest = w[2:]
            if ku == "kw" and (not rest or rest[0] not in VOWELS):
                continue
            neg_options = [(None, rest)]
            if rest.startswith("to"):
                neg_options.append(("to", rest[2:]))
            for neg, r1 in neg_options:
                om_options = [(None, r1)]
                for om in OBJECT_MARKERS:
                    if r1.startswith(om) and len(r1) > len(om):
                        nxt = r1[len(om)]
                        if (om == "mw" and nxt not in VOWELS) or (om == "m" and nxt in VOWELS):
                            continue
                        om_options.append((om, r1[len(om):]))
                for om, r2 in om_options:
                    for root, exts, fv, arabic in self._stems(r2, {"a"}):
                        # infinitive 'ku' is the marker, so vowelless roots are fine
                        if not root or (not _has_vowel(root) and (exts or fv != "a")):
                            continue
                        p = VerbParse(
                            word=w, form="infinitive", ku=ku, root=root, extensions=exts,
                            final_vowel=fv, object_marker=om,
                            object_labels=OBJECT_MARKERS.get(om, []), arabic_root=arabic,
                            tam=neg, tam_name="negative infinitive" if neg else None,
                            polarity="negative" if neg else "positive")
                        p.score = self._score(p, "inf")
                        if p.score > 0:
                            out.append(p)
        return out

    # ------------------------------------------------------------ imperative
    def _parse_imperative(self, w: str) -> List[VerbParse]:
        out: List[VerbParse] = []
        candidates = [(w, {"a"}, "singular")]
        if w.endswith("ni") and len(w) > 4:
            candidates.append((w[:-2], {"e"}, "plural"))
        for body, kinds, number in candidates:
            for root, exts, fv, arabic in self._stems(body, kinds):
                if not _has_vowel(root):
                    continue
                p = VerbParse(word=w, form="imperative", root=root, extensions=exts,
                              final_vowel=fv + ("ni" if number == "plural" else ""),
                              arabic_root=arabic, tam_name=f"imperative ({number})")
                p.score = self._score(p, "imp")
                if p.score > 0:
                    out.append(p)
        return out

    # ------------------------------------------------------------ stems
    def _stems(self, rest: str, kinds: Set[str]):
        """Yield (root, extensions, final_vowel, arabic) for root+ext+FV."""
        if len(rest) < 2:
            return
        last = rest[-1]
        if last in kinds:
            for root, exts in self._decompose(rest[:-1]):
                yield root, exts, last, False
        # Arabic-origin roots keep their own final vowel (-u always; -i only if known)
        if len(rest) >= 3 and (last == "u" or (last == "i" and rest in self.lexicon)):
            yield rest, [], "", True

    def _decompose(self, stem: str):
        """The stem as a bare root, then with 1..MAX_EXTENSIONS peeled off."""
        results = [(stem, [])]
        frontier = [(stem, [])]
        for _ in range(MAX_EXTENSIONS):
            nxt = []
            for cur, exts in frontier:
                for base, ext in self._peel(cur):
                    item = (base, [ext] + exts)
                    results.append(item)
                    nxt.append(item)
            frontier = nxt
        return results

    def _peel(self, stem: str):
        for label, high, mid in EXTENSIONS:
            for surface, is_mid in ((high, False), (mid, True)):
                if is_mid and mid == high:
                    continue
                if not stem.endswith(surface) or len(stem) == len(surface):
                    continue
                base = stem[:-len(surface)]
                lv = _last_vowel(base)
                # vowel harmony (only where the high and mid forms differ)
                if high != mid and lv is not None and ((lv in "eo") != is_mid):
                    continue
                if surface in ("i", "e") and base[-1] in VOWELS:
                    continue
                if surface in ("li", "le") and base[-1] not in VOWELS:
                    continue
                if surface in ("iw", "ew") and _has_vowel(base):
                    continue
                # -an- may follow a stacked vowel-final extension (pik-i-an-a)
                if surface in ("ik", "ek", "ish", "esh", "iz", "ez") and base[-1] in VOWELS:
                    continue
                if not _has_vowel(base) and (
                        surface[0] not in VOWELS or surface in ("ik", "ek", "an", "li", "le")):
                    continue
                yield base, (label, surface)

    # ------------------------------------------------------------ scoring
    def _plausible(self, root, exts, ku, polarity, tam_key) -> bool:
        if not root:
            return False
        if ku == "ku" and tam_key not in ("hu",):
            # monosyllabic ku-: vowelless root, no extension
            return not _has_vowel(root) and not exts
        if not _has_vowel(root):
            # vowelless roots stand alone only in the negative present / past (hali, hakula)
            return bool(exts) or tam_key in ("neg", "negku")
        return True

    def _score(self, p: VerbParse, tam_key: str) -> float:
        if p.form == "infinitive":
            s = 0.85
        elif p.form == "imperative":
            s = 0.45
        elif p.polarity == "negative":
            s = 0.95
        elif p.tam == "hu":
            s = 0.8
        elif p.relative_suffix:
            s = 0.8            # asomaye, wasomao (general-present relatives)
        elif p.tam is None:
            s = 0.65 if p.final_vowel == "e" else 0.55
        else:
            s = 0.95
        s -= 0.05 * len(p.extensions)
        if p.arabic_root:
            s -= 0.2
        if len(p.root) == 1 and _has_vowel(p.root):
            s -= 0.15

        # Phonotactic sanity: roots rarely look like this, so these usually
        # mean a prefix was mis-segmented into the root.
        if p.ku != "ku" and p.form != "infinitive" and p.root.startswith("ku"):
            s -= 0.1
        if re.match(r"m[bpfvtdkgcjszh]|n[dgjzt]", p.root):
            s -= 0.1
        if re.search(r"[aeiou]{2}", p.root):
            s -= 0.1
        if p.ku == "ku" and p.form != "infinitive":
            s += 0.02

        if self.lexicon:
            if p.root in self.lexicon:
                s += 0.4
                attested = self.verb_info.get(p.root, {}).get("exts")
                if p.extensions and attested and \
                        "".join(x for _, x in p.extensions) + p.final_vowel in attested:
                    s += 0.1                    # the dictionary lists exactly this derivation
                if _has_vowel(p.root):
                    # known base + extension beats a lexicalised derived stem
                    s += 0.07 * len(p.extensions)
            else:
                s -= 0.15
        if self.lexicon and not p.object_marker and any(
                p.root.startswith(om) and p.root[len(om):] in self.lexicon
                for om in OBJECT_MARKERS):
            s -= 0.1            # root looks like OM + known root (wap- = wa- + p-)
        if p.relative and not (self.lexicon and p.root in self.lexicon):
            s -= 0.02
        s += 0.01 * len(p.negative_prefix or p.subject_marker or "")
        return s
