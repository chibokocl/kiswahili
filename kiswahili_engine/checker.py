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
``PREP-KWA`` "kwa" before a place after a verb of motion ("enda kwa kituo" -> kwenye kituo / kituoni)
``STD-IMP``  non-standard imperative ("enda" -> "nenda")
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

# subject marker (+ tense) + relative particle with no root: walio, ambayo-like fragments
RELATIVE_PARTICLE = re.compile(r"^(wa|a|u|i|li|ya|ki|vi|zi|ku|pa|mu)(li|na|ta|me)?(ye|o|yo|lo|cho|vyo|zo|ko|po|mo)$")

# Verb roots meaning go / come / return / arrive / enter / pass (kwa + place is wrong after these)
MOTION_ROOTS = {"end", "nend", "j", "rud", "rudi", "fik", "ing", "ingi", "pit", "safir"}
# Common place nouns (hand-curated: the dictionary has no place flag, and lacks e.g. 'kituo').
# 'kwa' belongs with people (kwa daktari); places take 'kwenye' or the locative -ni.
PLACE_NOUNS = {
    "kituo", "shule", "soko", "hospitali", "zahanati", "kanisa", "msikiti", "ofisi", "benki",
    "duka", "mji", "kijiji", "shamba", "bustani", "uwanja", "nyumba", "chumba", "maktaba",
    "kiwanda", "gereza", "mahakama", "bandari", "kisiwa", "mtaa", "mgahawa", "hoteli",
    "chuo", "darasa", "jiko", "choo", "bafu", "pwani", "mlima", "mto", "ziwa", "msitu",
}

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
    # other words the issue is about (the noun a modifier must agree with), for highlighting
    related: List[Dict] = field(default_factory=list)

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


def _edit_distance(a: str, b: str, limit: float) -> float:
    """Edit cost tuned to typing errors, with early exit (returns > limit when too far).

    Insert/delete/substitute cost 1, except that adding or dropping a *doubled* letter
    (kiuu <-> kiu) costs 0.4 and a transposition (kitabu <-> kiatbu) costs 0.8.
    """
    if abs(len(a) - len(b)) > limit + 1:
        return limit + 1

    def dup(s: str, i: int) -> float:
        return 0.4 if (i > 0 and s[i - 1] == s[i]) or (i + 1 < len(s) and s[i + 1] == s[i]) else 1.0

    n, m = len(a), len(b)
    prev2 = None
    prev = [0.0]
    for j in range(1, m + 1):
        prev.append(prev[-1] + dup(b, j - 1))
    for i in range(1, n + 1):
        cur = [prev[0] + dup(a, i - 1)]
        for j in range(1, m + 1):
            best = min(prev[j] + dup(a, i - 1),                 # delete a[i-1]
                       cur[j - 1] + dup(b, j - 1),              # insert b[j-1]
                       prev[j - 1] + (0.0 if a[i - 1] == b[j - 1] else 1.0))
            if prev2 is not None and i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                best = min(best, prev2[j - 2] + 0.8)            # transposition
            cur.append(best)
        if min(cur) > limit:
            return limit + 1
        prev2, prev = prev, cur
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
        # prefix-only guess at a noun's morphological class (jitu -> 5/6, kijana -> 7/8)
        self._prefix_ns = EnhancedNgeliSystem(verb_parser=self.ns.verb_parser, use_noun_lexicon=False)
        self.known: Set[str] = {w for w, n in freq.items() if n >= min_freq and w.isalpha()}
        self._by_len: Dict[int, List[str]] = {}
        pool = set(self.known)
        if self.ns.noun_lexicon:          # dictionary nouns count as suggestions even if rare in the corpus
            pool |= {w for w in self.ns.noun_lexicon._index if w.isalpha() and len(w) > 2}
        for w in pool:
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
        issues += self._rule_prepositions(tokens, text)
        issues += self._rule_standard_forms(tokens)
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
            readings = self._readings(sw)
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
                # animate nouns of any class take a-/wa- agreement; only a noun the
                # dictionary shows to be inanimate (kitabu) can be flagged for it
                if marker_classes & {"1", "2"} and not lex.is_inanimate(sw):
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
                [Suggestion(fixed, f"agrees with '{subj.text}'")], confidence,
                related=[{"start": subj.start, "end": subj.end, "text": subj.text, "role": "subject"}]))
        return out

    def _readings(self, word: str) -> List[Tuple[str, str]]:
        """(ngeli, number) readings: the lexicon's, else an unattested ma- plural of a known
        word (masoda <- soda) read as 5/6 plural.  Attested words (mapema) never get this."""
        lex = self.ns.noun_lexicon
        found = lex.candidates(word) if lex else []
        if found:
            return found
        if (word.startswith("ma") and len(word) >= 6 and self.freq.get(word, 0) < 3
                and word[2] not in "aeiou"
                and (word[2:] in self.known or (lex and word[2:] in lex))):
            return [("5/6", "plural")]
        return []

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
            readings = self._readings(nw)
            forms = self.concord.lookup(mod.text)
            if not readings or not forms or lex.lookup(mod.text):
                continue                                   # unknown noun / not a concord word
            if self.concord.lookup(nw) or RELATIVE_PARTICLE.match(nw):
                continue                                   # 'noun' is itself zao / walio ...
            mod_classes = {f.cls for f in forms}
            if mod_classes <= LOCATIVE:
                continue                                   # kwa, pa, mwa: usually prepositions
            if i > 0 and tokens[i - 1].sentence == noun.sentence:
                # the modifier may belong to the word before the noun (kitega uchumi vyao);
                # only words that could be nouns count -- not verbs or short function words
                pw = _norm(tokens[i - 1].text)
                if len(pw) > 3 and not self.ns.verb_parser.is_finite_verb(pw) \
                        and not self.concord.lookup(pw):
                    prev = self.ns.identify_ngeli_enhanced(pw)
                    if prev and set(self._classes([(prev.ngeli_class, "singular"),
                                                   (prev.ngeli_class, "plural")])) & mod_classes:
                        continue
            noun_classes = self._classes(readings)
            if set(noun_classes) & mod_classes:
                continue                                   # agrees
            if any(r[0] in ("1/2", "1a/2a") for r in readings):
                # animate nouns also take the concord of their own prefix class (jitu kubwa)
                pre = self._prefix_ns.identify_ngeli_enhanced(nw)
                if pre and set(self._classes([(pre.ngeli_class, "singular"),
                                              (pre.ngeli_class, "plural")])) & mod_classes:
                    continue
            if mod_classes & {"1", "2"} and not lex.is_inanimate(nw):
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
                0.85 if len(noun_classes) == 1 else 0.75,
                related=[{"start": noun.start, "end": noun.end, "text": noun.text, "role": "noun"}]))
        return out

    # ------------------------------------------------------------------ PREP-KWA
    def _is_motion_verb(self, word: str) -> bool:
        for p in self.ns.verb_parser.parse(word)[:4]:
            if p.root in MOTION_ROOTS and p.score >= 0.4 \
                    and p.form in ("finite", "infinitive", "imperative"):
                return True
        return False

    def _rule_prepositions(self, tokens: List[_Token], text: str) -> List[Issue]:
        out = []
        for i in range(1, len(tokens) - 1):
            verb, kwa, place = tokens[i - 1], tokens[i], tokens[i + 1]
            if _norm(kwa.text) != "kwa" or not (verb.sentence == kwa.sentence == place.sentence):
                continue
            if text[verb.end:kwa.start].strip() or text[kwa.end:place.start].strip():
                continue                                   # punctuation in between
            noun = _norm(place.text)
            if noun not in PLACE_NOUNS or not self._is_motion_verb(verb.text):
                continue
            after = _norm(tokens[i + 2].text) if i + 2 < len(tokens) \
                and tokens[i + 2].sentence == place.sentence else ""
            options = [Suggestion(f"kwenye {place.text}", "place after a verb of motion")]
            if after not in CONNECTIVES:                   # kituoni cha afya would be wrong
                options.append(Suggestion(place.text + "ni", "locative -ni"))
            out.append(Issue(
                kwa.start, place.end, text[kwa.start:place.end], "PREP-KWA", "preposition",
                "warning",
                f"After a verb of motion, 'kwa' is used with people (kwa daktari). "
                f"For a place say 'kwenye {place.text}'"
                + ("" if after in CONNECTIVES else f" or '{place.text}ni'") + ".",
                f"'kwa' hutumika na watu (kwa daktari); mahali pasemwe 'kwenye {place.text}'"
                + ("" if after in CONNECTIVES else f' au \'{place.text}ni\'') + ".",
                options, 0.8,
                related=[{"start": verb.start, "end": verb.end, "text": verb.text, "role": "verb"}]))
        return out

    # ------------------------------------------------------------------ STD-IMP
    def _rule_standard_forms(self, tokens: List[_Token]) -> List[Issue]:
        out = []
        for i, t in enumerate(tokens):
            if t.text.lower() != "enda":
                continue
            opens = t.first_in_sentence or (
                i > 0 and tokens[i - 1].sentence == t.sentence and _norm(tokens[i - 1].text) == "tafadhali")
            if not opens:                                  # 'enda' elsewhere may be a stem/other form
                continue
            fixed = "Nenda" if t.text[0].isupper() else "nenda"
            out.append(Issue(
                t.start, t.end, t.text, "STD-IMP", "standard", "info",
                "The standard imperative of kwenda is 'nenda'; 'enda' is older or biblical style.",
                "Amri ya 'kwenda' katika Kiswahili sanifu ni 'nenda'.",
                [Suggestion(fixed)], 0.65))
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
        if self._is_locative(w):
            return True
        return self._plausible_verb(w) or self._is_noun_variant(w)

    def _is_locative(self, w: str) -> bool:
        """Locative -ni: shuleni, kituoni, hospitalini, mjini ('mji' + ni)."""
        if not w.endswith("ni") or len(w) < 5:
            return False
        lex = self.ns.noun_lexicon
        for stem in (w[:-2], w[:-2] + "o", w[:-2] + "e", w[:-2] + "a"):  # nyumbani, soko-ni ...
            if stem in self.known or (lex and stem in lex):
                return True
        return False

    def suggest(self, word: str, limit: int = 3) -> List[Tuple[str, float]]:
        """Nearest known words as (word, cost), most likely first."""
        if word in self._suggest_cache:
            return self._suggest_cache[word][:limit]
        max_d = 1.0 if len(word) <= 4 else 2.0
        cands = []
        for L in range(max(len(word) - 2, 3 if len(word) >= 4 else 1), len(word) + 3):
            for w in self._by_len.get(L, ()):
                d = _edit_distance(word, w, max_d)
                if d <= max_d:
                    cands.append((d, -math.log1p(self.freq.get(w, 1)), w))
        cands.sort()
        res = [(w, d) for d, _, w in cands]
        self._suggest_cache[word] = res
        return res[:limit] if limit else res

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
                confidence = 0.8 if best[1] <= 1 else 0.65
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
