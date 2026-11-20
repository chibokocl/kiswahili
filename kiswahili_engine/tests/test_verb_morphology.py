"""Tests for the slot-based verb parser."""

import unittest
from pathlib import Path

from kiswahili_engine.core.verb_morphology import VerbParser
from kiswahili_engine.core.ngeli_system import EnhancedNgeliSystem
from kiswahili_engine import create_engine

CORPUS_WORDS = Path(__file__).resolve().parents[2] / "swahili_corpus" / "swahili_words.txt"


class TestVerbParser(unittest.TestCase):
    """Top-ranked segmentation (no lexicon) for unambiguous verbs."""

    def setUp(self):
        self.parser = VerbParser()

    def seg(self, word, **kw):
        return self.parser.best(word, **kw).segmentation()

    def test_basic_tenses(self):
        cases = {
            "wanasoma": "wa-na-som-a", "alisoma": "a-li-som-a",
            "amesoma": "a-me-som-a", "atasoma": "a-ta-som-a",
            "akasoma": "a-ka-som-a", "tukisoma": "tu-ki-som-a",
            "nasoma": None,  # 'na' alone is not a subject+TAM; just must not crash
        }
        for word, expected in cases.items():
            if expected:
                self.assertEqual(self.seg(word), expected, word)

    def test_monosyllabic_ku(self):
        self.assertEqual(self.seg("anakula"), "a-na-ku-l-a")
        self.assertEqual(self.seg("anakuja"), "a-na-ku-j-a")
        self.assertEqual(self.seg("alikuwa"), "a-li-ku-w-a")
        self.assertEqual(self.seg("hakuja"), "ha-ku-j-a")
        self.assertEqual(self.seg("hakula"), "ha-ku-l-a")

    def test_negatives(self):
        self.assertEqual(self.seg("hasomi"), "ha-som-i")
        self.assertEqual(self.seg("sisomi"), "si-som-i")
        self.assertEqual(self.seg("hatupendi"), "hatu-pend-i")
        self.assertEqual(self.seg("hakusoma"), "ha-ku-som-a")
        self.assertEqual(self.seg("hatasoma"), "ha-ta-som-a")
        self.assertEqual(self.seg("hajasoma"), "ha-ja-som-a")
        self.assertEqual(self.best("hali").polarity, "negative")

    def best(self, w):
        return self.parser.best(w)

    def test_object_markers(self):
        p = self.best("atakupenda")
        self.assertEqual((p.object_marker, p.root), ("ku", "pend"))
        p = self.best("alimpiga")
        self.assertEqual((p.object_marker, p.root), ("m", "pig"))
        p = self.best("nimemwona")
        self.assertIn(p.segmentation(), ("ni-me-mwon-a", "ni-me-mw-on-a"))

    def test_relative(self):
        p = self.best("kinachoanguka")
        self.assertEqual((p.relative, p.root), ("cho", "anguk"))
        p = self.best("wasomao")
        self.assertEqual(p.relative_suffix, "o")

    def test_habitual_and_infinitive(self):
        self.assertEqual(self.best("husoma").tam_name, "habitual")
        p = self.best("kusoma")
        self.assertEqual((p.form, p.root), ("infinitive", "som"))
        p = self.best("kwenda")
        self.assertEqual((p.form, p.root), ("infinitive", "end"))
        self.assertEqual(self.best("kunywa").root, "nyw")

    def test_extensions_are_among_candidates(self):
        segs = [p.segmentation() for p in self.parser.parse("alipikiwa")]
        self.assertIn("a-li-pik-i-w-a", segs)
        segs = [p.segmentation() for p in self.parser.parse("wanasomeshwa")]
        self.assertIn("wa-na-som-esh-w-a", segs)
        segs = [p.segmentation() for p in self.parser.parse("analiwa")]
        self.assertIn("a-na-l-iw-a", segs)       # passive of monosyllabic kula
        segs = [p.segmentation() for p in self.parser.parse("tutaonana")]
        self.assertIn("tu-ta-on-an-a", segs)      # reciprocal

    def test_vowel_harmony(self):
        # som + e (not +i) after an o-vowel; pend + e is not a valid applicative
        segs = [p.segmentation() for p in self.parser.parse("anasomea")]
        self.assertIn("a-na-som-e-a", segs)
        self.assertNotIn("a-na-som-i-a", segs)

    def test_subject_labels_and_ngeli(self):
        self.assertIn(("7/8", "singular"), self.best("kilianguka").subject_ngeli())
        self.assertIn(("1/2", "plural"), self.best("wanasoma").subject_ngeli())

    def test_subject_hint_disambiguates(self):
        # 'u' is class 3/11/14 and 2sg; hint prefers the agreeing reading
        p = self.parser.best("unasoma", subject=("3/4", "singular"))
        self.assertIn(("3/4", "singular"), p.subject_ngeli())

    def test_nouns_are_not_verbs(self):
        for noun in ["wanafunzi", "watoto", "kitabu", "mkate", "mwalimu", "nyumba"]:
            self.assertFalse(self.parser.is_finite_verb(noun), noun)

    def test_arabic_root(self):
        p = self.best("anafahamu")
        self.assertTrue(p.arabic_root)
        self.assertEqual(p.root, "fahamu")
        self.assertTrue(self.parser.is_finite_verb("anafahamu"))

    def test_garbage_input(self):
        for w in ["", "a", "xyz", "'", "ku", "1234"]:
            self.parser.parse(w)  # must not raise


@unittest.skipUnless(CORPUS_WORDS.exists(), "corpus not available")
class TestVerbParserWithLexicon(unittest.TestCase):
    """A corpus-derived root lexicon resolves root/extension ambiguity."""

    @classmethod
    def setUpClass(cls):
        cls.parser = VerbParser.from_wordlist(CORPUS_WORDS)

    def test_lexicon_loaded(self):
        self.assertGreater(len(self.parser.lexicon), 1000)
        self.assertIn("som", self.parser.lexicon)

    def test_extension_resolved(self):
        self.assertEqual(self.parser.best("alipikiwa").segmentation(), "a-li-pik-i-w-a")
        self.assertEqual(self.parser.best("wanasomeshwa").segmentation(), "wa-na-som-esh-w-a")

    def test_object_marker_resolved(self):
        self.assertEqual(self.parser.best("nimemwona").segmentation(), "ni-me-mw-on-a")


class TestEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.ns = EnhancedNgeliSystem()

    def test_verb_structure_dict(self):
        r = self.ns.analyze_verb_structure_enhanced("hawasomi")
        self.assertEqual(r["structure"]["subject_prefix"], "hawa")
        self.assertEqual(r["structure"]["root"], "som")
        self.assertEqual(r["structure"]["polarity"], "negative")
        self.assertEqual(r["tense"], "negative present")

    def test_noun_has_no_verb_analysis(self):
        r = self.ns.analyze_verb_structure_enhanced("wanafunzi")
        self.assertIsNone(r["tense"])

    def test_agreement_detects_mismatch(self):
        ok = self.ns.check_enhanced_agreement("kitabu", "kimeanguka")
        bad = self.ns.check_enhanced_agreement("kitabu", "wameanguka")
        self.assertTrue(ok["verb_agreement"])
        self.assertFalse(bad["verb_agreement"])

    def test_negative_agreement(self):
        r = self.ns.check_enhanced_agreement("watoto", "hawasomi")
        self.assertTrue(r["verb_agreement"])

    def test_sentence_no_longer_treats_nouns_as_verbs(self):
        # 'wanafunzi' contains 'na'; the old substring heuristic took it for a verb
        r = create_engine().analyze_sentence_enhanced("Wanafunzi wamesoma vitabu")
        self.assertEqual(r["structure"]["kiima"], ["Wanafunzi"])
        self.assertEqual(r["structure"]["kiarifu"][0], "wamesoma")


if __name__ == "__main__":
    unittest.main()


class TestKamusiVerbLexicon(unittest.TestCase):
    """Dictionary-derived roots (data/verb_lexicon.json) and their builder."""

    @classmethod
    def setUpClass(cls):
        cls.parser = VerbParser.from_kamusi()

    def test_roots_loaded(self):
        self.assertGreater(len(self.parser.lexicon), 3000)
        for root in ("som", "pik", "anguk", "l", "nyw"):
            self.assertTrue(self.parser.is_known_root(root), root)
        self.assertTrue(self.parser.is_known_root("jibu"))          # Arabic-origin surface form
        self.assertIn("ia", self.parser.verb_info["pik"]["exts"])    # attested applicative

    def test_attested_extension_wins(self):
        self.assertEqual(self.parser.best("anapikiwa").segmentation(), "a-na-pik-i-w-a")
        self.assertEqual(self.parser.best("anaachisha").segmentation(), "a-na-ach-ish-a")

    def test_stacked_reciprocal_after_applicative(self):
        segs = [p.segmentation() for p in VerbParser().parse("anapikiana")]
        self.assertIn("a-na-pik-i-an-a", segs)

    def test_retarget_subject(self):
        p = self.parser.best("umeanguka")
        self.assertEqual(p.retarget_subject("7/8", "singular"), "kimeanguka")
        self.assertEqual(self.parser.best("hawasomi").retarget_subject("7/8", "singular"), "hakisomi")
        self.assertEqual(self.parser.best("anacheza").retarget_subject("1/2", "plural"), "wanacheza")


class TestVerbBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
        import build_verb_lexicon as b
        cls.b = b

    def parse(self, text):
        entries, stats = self.b.parse(text)
        return {(e["root"], e["fv"]): e for e in entries}

    def test_dotted_headword_extensions_and_transitivity(self):
        got = self.parse("end.a kt -ele- 1. toka pahali. (~ea, ~eka,\n~esha, ~ewa)\nabir.i1 kt -sie- safiri\n")
        e = got[("end", "a")]
        self.assertEqual((e["dotted"], e["trans"], e["exts"]), (True, ["ele"], ["ea", "eka", "esha", "ewa"]))
        self.assertEqual(got[("abir", "i")]["trans"], ["sie"])

    def test_dotless_and_both_transitivities(self):
        got = self.parse("fotoa kt -ele- piga picha\nish.a2 kt -ele-/-sie- 1. fikia mwisho\n")
        self.assertEqual(got[("foto", "a")]["dotted"], False)
        self.assertEqual(got[("ish", "a")]["trans"], ["ele", "sie"])

    def test_extensions_do_not_leak_into_next_entry(self):
        got = self.parse("a.a kt -ele- toa\nb.a kt -ele- leta (~ia)\n")
        self.assertEqual(got[("a", "a")]["exts"], [])
