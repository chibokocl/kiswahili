"""
Kiswahili writing checker ("Grammarly for Kiswahili").

    from kiswahili_engine.checker import Checker
    for issue in Checker().check("kitabu umeanguka."):
        print(issue.rule, issue.text, issue.suggestions)

Every :class:`Issue` carries a character span, a rule id, an explanation in English
and Kiswahili, ranked suggestions and a confidence.  The checker is **precision
first**: a writing assistant that cries wolf on correct Kiswahili is worse than one
that misses errors, so each rule only fires where it can be confident, and
``check(min_confidence=...)`` lets callers tighten or loosen that.

Rules
-----
``AGR-SV``   subject-verb agreement ("Kitabu umeanguka" -> kimeanguka)
``SPELL``    likely misspelling, with ranked corrections
``AGR-NA``   noun-modifier concord: adjectives, numerals, possessives, connective -a
             ("kitabu mzuri" -> kizuri, "kitabu wa mtoto" -> cha mtoto)
``CAP``      sentence-initial capital

Deliberate blind spots (to avoid false alarms): animate nouns of any class may take
a-/wa- agreement; a singular human noun may take a plural verb out of respect
(Mwalimu wamefika); adverbial nouns (leo, jana, nyumbani...) are not treated as subjects;
only the pattern ``<sentence-start noun> <verb>`` is checked for agreement.
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import argparse
import json
import math
import re

from .core.ngeli_system import EnhancedNgeliSystem
from .core.verb_morphology import VERB_THRESHOLD
from .core.concord import ConcordLexicon
from .data.verb_data import CLASS_TO_NGELI

DEFAULT_CORPUS = Path(__file__).resolve().parent.parent / "swahili_corpus" / "swahili_corpus.json"

WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*")
SENTENCE_END = re.compile(r"[.!?]")

# Nouns that open sentences as adverbials ("Leo anakuja"): the real subject is elsewhere.
ADVERBIAL_NOUNS = {
    "leo", "jana", "kesho", "juzi", "sasa", "asubuhi", "mchana", "jioni", "usiku", "alfajiri",
    "wakati", "baadaye", "zamani", "mwaka", "mwezi", "wiki", "siku", "hapa", "pale", "huko",
    "kule", "mahali", "pahali", "nyumbani", "shuleni", "mjini", "kijijini", "mbele", "nyuma",
    "juu", "chini", "ndani", "nje", "karibu", "mbali", "kando", "baada", "kabla", "tangu",
    "hadi", "mara", "kisha", "halafu", "tena", "hivyo", "kwanza", "mwishowe", "pia",
}


# Words that look like nouns but open sentences as pronouns/demonstratives/quantifiers
DETERMINERS = {
    "huyu", "huyo", "yule", "hawa", "hao", "wale", "hiki", "hicho", "kile", "hivi", "hivyo",
    "vile", "hii", "hiyo", "ile", "hizi", "hizo", "zile", "huu", "huo", "ule", "hili", "hilo",
    "lile", "haya", "hayo", "yale", "huku", "huko", "kule", "hapo", "mimi", "wewe", "yeye",
    "sisi", "nyinyi", "wao", "wote", "yote", "zote", "vyote", "kila", "baadhi", "wengi",
    "wengine", "mmoja", "pili", "tatu", "nne", "tano", "kwanza", "yoyote", "chochote",
}

# Common English words appear in Kiswahili text (quotes, titles); never flag them as typos.
ENGLISH = set("""a an the and or of in on at to for from by with as is are was were be been it its
this that these those not no yes but if so we you he she they i my your his her their our us
public company act account balance sheet profit loss corporations newspapers publish page
es in the""".split())

NOUN_PREFIXES = ("wa", "mi", "ma", "ki", "vi", "ch", "vy", "ji", "mw", "mu", "m", "u")
# -a forms that open genitive chains: "mkuu wa shule nzuri" is ambiguous, so skip those
CONNECTIVES = {"wa", "ya", "la", "cha", "vya", "za", "kwa", "pa", "mwa"}
# forms in these classes only are often just prepositions (kwa, pa, mwa) -- never flag them
LOCATIVE = {"15", "16", "17", "18"}
# classes whose nouns are practically never animate (no a-/wa- concord to forgive)
INANIMATE_ONLY = {"3", "4", "11", "14", "15", "16", "17", "18"}

# subject marker (+ tense) + relative particle with no root: walio, ambayo-like fragments
RELATIVE_PARTICLE = re.compile(r"^(wa|a|u|i|li|ya|ki|vi|zi|ku|pa|mu)(li|na|ta|me)?(ye|o|yo|lo|cho|vyo|zo|ko|po|mo)$")

ROMAN = re.compile(r"^[ivxlc]+$", re.I)


@dataclass
class Suggestion:
    text: str
    note: str = ""


@dataclass
class Issue:
    start: int
    end: int
    text: str
    rule: str
    category: str                     # agreement | spelling | capitalization
    severity: str                     # error | warning | info
    message: str
    message_sw: str
    suggestions: List[Suggestion] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class _Token:
    text: str
    start: int
    end: int
    sentence: int
    first_in_sentence: bool = False


def tokenize(text: str) -> List[_Token]:
    tokens: List[_Token] = []
    sentence, prev_end = 0, 0
    for m in WORD.finditer(text):
        gap = text[prev_end:m.start()]
        first = not tokens
        if tokens and SENTENCE_END.search(gap):
            sentence += 1
            first = True
        tokens.append(_Token(m.group(), m.start(), m.end(), sentence, first))
        prev_end = m.end()
    return tokens


def _norm(w: str) -> str:
    return w.lower().replace("’", "'")


def _edit_distance(a: str, b: str, limit: int) -> int:
    """Levenshtein with early exit; returns limit+1 when the distance exceeds ``limit``."""
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > limit:
            return limit + 1
        prev = cur
    return prev[-1]


class Checker:
    """Runs all rules over a text and returns :class:`Issue` objects sorted by position."""

    def __init__(self, ngeli_system: Optional[EnhancedNgeliSystem] = None,
                 corpus_path=None, min_freq: int = 3):
        self.ns = ngeli_system or EnhancedNgeliSystem()
        path = Path(corpus_path) if corpus_path else DEFAULT_CORPUS
        freq: Dict[str, int] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        self.min_freq = min_freq
        self.freq = freq
        self.concord = ConcordLexicon.load()
        self.known: Set[str] = {w for w, n in freq.items() if n >= min_freq and w.isalpha()}
        self._by_len: Dict[int, List[str]] = {}
        for w in self.known:
            self._by_len.setdefault(len(w), []).append(w)
        self._suggest_cache: Dict[str, List[Tuple[str, int]]] = {}
        # stems of known nouns, so noun-class variants (watekelezaji ~ utekelezaji) are accepted
        self._stems: Set[str] = set()
        nouns = list(self.ns.noun_lexicon._index) if self.ns.noun_lexicon else []
        for w in list(self.known) + nouns:
            for rest in self._strip_prefix(w):
                self._stems.add(rest)

    # ------------------------------------------------------------------ API
    def check(self, text: str, min_confidence: float = 0.6) -> List[Issue]:
        tokens = tokenize(text)
        issues: List[Issue] = []
        issues += self._rule_capitalization(tokens, text)
        issues += self._rule_agreement(tokens)
        issues += self._rule_concord(tokens, text)
        issues += self._rule_spelling(tokens)
        issues = [i for i in issues if i.confidence >= min_confidence]
        issues.sort(key=lambda i: (i.start, i.end))
        return issues

    # ------------------------------------------------------------------ CAP
    def _rule_capitalization(self, tokens: List[_Token], text: str) -> List[Issue]:
        out = []
        for i, t in enumerate(tokens):
            if not t.first_in_sentence or not t.text[0].islower() or len(t.text) < 2:
                continue
            if ROMAN.match(t.text):                      # (ii) (iii) list numbering
                continue
            before = text[:t.start].rstrip(" \t")
            if before and before[-1] in "(\"“‘'[:;,":    # parenthetical / quoted / mid-list
                continue
            # "n.k.", "k.m." style abbreviations end a 'sentence' without ending one
            if i > 0 and len(tokens[i - 1].text) <= 2:
                continue
            fixed = t.text[0].upper() + t.text[1:]
            out.append(Issue(
                t.start, t.end, t.text, "CAP", "capitalization", "warning",
                "Sentences start with a capital letter.",
                "Sentensi huanza kwa herufi kubwa.",
                [Suggestion(fixed)], 0.9))
        return out

    # ------------------------------------------------------------------ AGR-SV
    def _rule_agreement(self, tokens: List[_Token]) -> List[Issue]:
        out = []
        lex, vp = self.ns.noun_lexicon, self.ns.verb_parser
        if not lex:
            return out
        for i in range(1, len(tokens)):
            subj, verb = tokens[i - 1], tokens[i]
            if subj.sentence != verb.sentence or not subj.first_in_sentence:
                continue
            sw = _norm(subj.text)
            if sw in ADVERBIAL_NOUNS or sw in DETERMINERS or sw.endswith("ni"):
                continue
            readings = lex.candidates(sw)
            if not readings:
                continue
            parse = vp.best(verb.text)
            if not (parse and parse.form == "finite" and parse.score >= VERB_THRESHOLD
                    and (parse.tam or parse.polarity == "negative")):
                continue
            if lex.lookup(verb.text):          # the 'verb' is also a noun (e.g. 'mama')
                continue
            sm_readings = parse.subject_ngeli()
            if not sm_readings:                # person-only marker (ni-, m-): not our business
                continue
            labels = set(parse.subject_labels)
            if labels & {"1sg", "1pl"}:        # "Sisi tutajenga", "Wananchi tunaomba": 1st person
                continue
            if "2sg" in labels and any(r[0] in ("1/2", "1a/2a") for r in readings):
                continue                       # vocative: "Mtoto unafanya nini?"
            if not self.ns.verb_parser.is_known_root(parse.root):
                continue                       # unfamiliar word: may not be a verb at all
            if any(r in sm_readings for r in readings):
                continue

            human = [r for r in readings if r[0] in ("1/2", "1a/2a")]
            marker_classes = set(parse.subject_labels)
            if not human:
                # animate nouns of any class take a-/wa- agreement
                if marker_classes & {"1", "2"}:
                    continue
            else:
                # singular human noun + plural verb = respect plural (Mwalimu wamefika)
                if ("1/2", "singular") in readings and "2" in marker_classes:
                    continue
            target = readings[0]
            fixed = parse.retarget_subject(*target)
            if not fixed:
                continue
            marker = parse.negative_prefix or parse.subject_marker
            new_marker = fixed[:len(fixed) - len(verb.text) + len(marker)]
            cls_name = f"{target[0]} ({target[1]})"
            confidence = 0.9 if len(readings) == 1 else 0.8
            out.append(Issue(
                verb.start, verb.end, verb.text, "AGR-SV", "agreement", "error",
                f"'{subj.text}' is in ngeli {cls_name}, so the verb needs the subject marker "
                f"'{new_marker}-', not '{marker}-'.",
                f"'{subj.text}' ni ya ngeli ya {target[0]}; kitenzi kianze kwa '{new_marker}-', "
                f"si '{marker}-'.",
                [Suggestion(fixed, f"agrees with '{subj.text}'")], confidence))
        return out

    # ------------------------------------------------------------------ AGR-NA
    @staticmethod
    def _classes(readings) -> List[str]:
        out: List[str] = []
        for ngeli, number in readings:
            for cls, rs in CLASS_TO_NGELI.items():
                if (ngeli, number) in rs and cls not in out:
                    out.append(cls)
        return out

    def _rule_concord(self, tokens: List[_Token], text: str) -> List[Issue]:
        out = []
        lex = self.ns.noun_lexicon
        if not lex:
            return out
        for i in range(len(tokens) - 1):
            noun, mod = tokens[i], tokens[i + 1]
            if noun.sentence != mod.sentence or text[noun.end:mod.start].strip():
                continue                                   # punctuation between them
            if i > 0 and tokens[i - 1].sentence == noun.sentence \
                    and _norm(tokens[i - 1].text) in CONNECTIVES:
                continue                                   # genitive chain: attachment unclear
            nw = _norm(noun.text)
            if (noun.text[0].isupper() and not noun.first_in_sentence) or nw in DETERMINERS \
                    or nw in ADVERBIAL_NOUNS or nw.endswith("ni"):
                continue
            readings = lex.candidates(nw)
            forms = self.concord.lookup(mod.text)
            if not readings or not forms or lex.lookup(mod.text):
                continue                                   # unknown noun / not a concord word
            if self.concord.lookup(nw) or RELATIVE_PARTICLE.match(nw):
                continue                                   # 'noun' is itself zao / walio ...
            mod_classes = {f.cls for f in forms}
            if mod_classes <= LOCATIVE:
                continue                                   # kwa, pa, mwa: usually prepositions
            if i > 0 and tokens[i - 1].sentence == noun.sentence:
                # the modifier may belong to the word before the noun (kitega uchumi vyao)
                prev = self.ns.identify_ngeli_enhanced(_norm(tokens[i - 1].text))
                if prev and set(self._classes([(prev.ngeli_class, "singular"),
                                               (prev.ngeli_class, "plural")])) & mod_classes:
                    continue
            noun_classes = self._classes(readings)
            if set(noun_classes) & mod_classes:
                continue                                   # agrees
            if mod_classes & {"1", "2"} and not set(noun_classes) <= INANIMATE_ONLY:
                continue                                   # animate noun of any class: a-/wa- concord
            if set(noun_classes) == {"1"} and "2" in mod_classes:
                continue                                   # respect plural: Mwalimu wetu wapya
            target = noun_classes[0]
            form = forms[0]
            fixed = self.concord.inflect(form, target)
            if not fixed or fixed == _norm(mod.text):
                continue
            if form.kind == "adjective" and self.freq.get(fixed, 0) < 2:
                continue                                   # generated form not attested: don't guess
            if mod.text[0].isupper():
                fixed = fixed.capitalize()
            what = {"adjective": "adjective", "connective": "connective -a",
                    "possessive": "possessive", "quantifier": "quantifier"}[form.kind]
            out.append(Issue(
                mod.start, mod.end, mod.text, "AGR-NA", "agreement", "error",
                f"'{noun.text}' is in class {target}, so the {what} should be '{fixed}', "
                f"not '{mod.text}'.",
                f"'{noun.text}' ni ya ngeli ya {target}; neno hili lipaswe kuwa '{fixed}', "
                f"si '{mod.text}'.",
                [Suggestion(fixed, f"agrees with '{noun.text}'")],
                0.85 if len(noun_classes) == 1 else 0.75))
        return out

    # ------------------------------------------------------------------ SPELL
    @staticmethod
    def _strip_prefix(w: str):
        for pre in NOUN_PREFIXES:
            if w.startswith(pre) and len(w) - len(pre) >= 4:
                yield w[len(pre):]

    def _plausible_verb(self, w: str) -> bool:
        """A structurally valid verb: known root in any finite form, or an unknown root
        only where the tense/negation marking makes the parse confident."""
        p = self.ns.verb_parser.best(w)
        if not p or p.form not in ("finite", "infinitive"):
            return False
        if self.ns.verb_parser.is_known_root(p.root) and p.score >= 0.6:
            return True
        return p.score >= VERB_THRESHOLD and bool(
            p.tam or p.polarity == "negative" or p.form == "infinitive" or p.relative_suffix)

    def _is_noun_variant(self, w: str) -> bool:
        lex = self.ns.noun_lexicon
        for rest in self._strip_prefix(w):
            if rest in self.known or rest in self._stems or (lex and rest in lex):
                return True
        return False

    def _is_known(self, w: str, token: str) -> bool:
        if len(w) <= 1 or token[0].isupper():          # letters, names, acronyms
            return True
        if w in ENGLISH or ROMAN.match(w) or w in self.concord:
            return True
        if w in self.known or (self.ns.noun_lexicon and w in self.ns.noun_lexicon):
            return True
        return self._plausible_verb(w) or self._is_noun_variant(w)

    def suggest(self, word: str, limit: int = 3) -> List[Tuple[str, int]]:
        """Nearest known words as (word, distance), most likely first."""
        if word in self._suggest_cache:
            return self._suggest_cache[word][:limit]
        max_d = 1 if len(word) <= 4 else 2
        cands = []
        for L in range(len(word) - max_d, len(word) + max_d + 1):
            for w in self._by_len.get(L, ()):
                d = _edit_distance(word, w, max_d)
                if d <= max_d:
                    cands.append((d, -math.log1p(self.freq.get(w, 1)), w))
        cands.sort()
        res = [(w, d) for d, _, w in cands]
        self._suggest_cache[word] = res
        return res[:limit]

    def _rule_spelling(self, tokens: List[_Token]) -> List[Issue]:
        out = []
        for t in tokens:
            w = _norm(t.text)
            if self._is_known(w, t.text):
                continue
            sugg = self.suggest(w)
            # Evidence of a typo = a close, frequent neighbour.  Unknown words with no
            # neighbour are far more likely to be rare words, foreign words or names.
            if sugg:
                best = sugg[0]
                confidence = 0.8 if best[1] == 1 else 0.65
                out.append(Issue(
                    t.start, t.end, t.text, "SPELL", "spelling", "warning",
                    f"'{t.text}' is not a known word. Did you mean '{best[0]}'?",
                    f"'{t.text}' haijulikani. Je, ulimaanisha '{best[0]}'?",
                    [Suggestion(s) for s, _ in sugg], confidence))
            else:
                out.append(Issue(
                    t.start, t.end, t.text, "SPELL", "spelling", "info",
                    f"'{t.text}' is not in the dictionary (it may be a rare or foreign word).",
                    f"'{t.text}' haimo kwenye kamusi.", [], 0.3))
        return out


def apply_suggestions(text: str, issues: List[Issue]) -> str:
    """Apply the first suggestion of every non-overlapping issue (right to left)."""
    out, last = text, len(text) + 1
    for i in sorted(issues, key=lambda i: -i.start):
        if i.suggestions and i.end <= last:
            out = out[:i.start] + i.suggestions[0].text + out[i.end:]
            last = i.start
    return out


def format_issues(text: str, issues: List[Issue]) -> str:
    lines = []
    for i in issues:
        fix = f"  ->  {', '.join(s.text for s in i.suggestions[:3])}" if i.suggestions else ""
        lines.append(f"[{i.rule}] {i.text!r} @{i.start}-{i.end} ({i.confidence:.2f}){fix}\n    {i.message}")
    return "\n".join(lines) if lines else "No issues found."


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check Kiswahili text")
    ap.add_argument("text", nargs="?", help="text to check (reads stdin if omitted)")
    ap.add_argument("--min-confidence", type=float, default=0.6)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    text = args.text if args.text is not None else __import__("sys").stdin.read()
    issues = Checker().check(text, args.min_confidence)
    if args.json:
        print(json.dumps([i.to_dict() for i in issues], ensure_ascii=False, indent=2))
    else:
        print(format_issues(text, issues))
        if issues:
            print("\nCorrected:", apply_suggestions(text, issues))


if __name__ == "__main__":
    main()
