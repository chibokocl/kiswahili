"""Tests for noun-class concord generation, the adjective lexicon, and the AGR-NA rule."""

import sys
import unittest
from pathlib import Path

from kiswahili_engine.checker import Checker
from kiswahili_engine.core.concord import ConcordLexicon, adjective_form, pronominal_form


class TestGenerator(unittest.TestCase):
    def test_adjective_paradigms(self):
        expected = {
            "zuri": {"1": "mzuri", "2": "wazuri", "4": "mizuri", "6": "mazuri", "7": "kizuri",
                     "8": "vizuri", "9": "nzuri"},
            "eupe": {"1": "mweupe", "2": "weupe", "4": "myeupe", "5": "jeupe", "6": "meupe",
                     "7": "cheupe", "8": "vyeupe", "9": "nyeupe"},
            "ingi": {"1": "mwingi", "2": "wengi", "4": "mingi", "6": "mengi", "7": "kingi",
                     "8": "vingi", "9": "nyingi"},
            "refu": {"1": "mrefu", "2": "warefu", "7": "kirefu", "9": "ndefu"},
            "pya": {"1": "mpya", "5": "jipya", "7": "kipya", "9": "mpya"},
            "ema": {"1": "mwema", "5": "jema", "7": "chema", "9": "njema"},
            "wili": {"2": "wawili", "9": "mbili"},
        }
        for stem, forms in expected.items():
            for cls, word in forms.items():
                self.assertEqual(adjective_form(stem, cls), word, f"-{stem} class {cls}")

    def test_pronominal(self):
        self.assertEqual([pronominal_form("a", c) for c in ("1", "4", "5", "7", "8", "10", "15")],
                         ["wa", "ya", "la", "cha", "vya", "za", "kwa"])
        self.assertEqual(pronominal_form("angu", "7"), "changu")
        self.assertEqual(pronominal_form("ote", "8"), "vyote")


class TestLexicon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cl = ConcordLexicon.load()

    def test_stems_loaded(self):
        for s in ("zuri", "kubwa", "dogo", "eupe", "ingi"):
            self.assertIn(s, self.cl.stems)

    def test_recognition_by_surface_form(self):
        forms = {(f.stem, f.cls) for f in self.cl.lookup("kizuri")}
        self.assertEqual(forms, {("zuri", "7")})
        self.assertIn("1", {f.cls for f in self.cl.lookup("mzuri")})
        self.assertEqual(self.cl.lookup("zzzz"), [])

    def test_invariable_adjectives(self):
        self.assertTrue(self.cl.is_invariable("adimu"))


class TestRule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chk = Checker()

    def fixes(self, text):
        return [(i.text, i.suggestions[0].text) for i in self.chk.check(text) if i.rule == "AGR-NA"]

    def test_errors_are_caught_with_fix(self):
        self.assertEqual(self.fixes("Alipanda miti mzuri."), [("mzuri", "mizuri")])
        self.assertEqual(self.fixes("Mtoto kizuri alikuja."), [("kizuri", "mzuri")])

    def test_correct_phrases_are_silent(self):
        for s in ["Kitabu kizuri kimeanguka.", "Alipanda miti mizuri.", "Watoto wadogo wanacheza.",
                  "Nyumba nzuri ni kubwa.", "Alinunua vitabu vitatu.", "Kitabu cha mtoto.",
                  "Nyumba yangu ni kubwa.", "Mti mrefu umeanguka."]:
            self.assertEqual(self.fixes(s), [], s)

    def test_false_alarm_traps(self):
        traps = {
            "animate noun, class 1 concord": "Ng'ombe mkubwa analala.",
            "human noun in 7/8": "Kijana mzuri amefika.",
            "respect plural": "Mwalimu wetu wapya wamefika.",
            "preposition kwa": "Alienda nyumbani kwa mwalimu.",
            "genitive chain": "Mwalimu wa shule nzuri amefika.",
            "punctuation between": "Alinunua kitabu, mzuri sana.",
            "compound / earlier head": "Hii ni kitega uchumi vyao.",
            "noun-noun": "Aliumia mwili wake.",
        }
        for name, s in traps.items():
            self.assertEqual(self.fixes(s), [], name)

    def test_generated_form_must_be_attested(self):
        # no suggestion that the corpus has never seen
        issues = self.chk.check("Alipanda miti mzuri.")
        for i in issues:
            if i.rule == "AGR-NA":
                self.assertGreaterEqual(self.chk.freq.get(i.suggestions[0].text, 0), 2)


class TestAdjectiveBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
        import build_adjective_lexicon as b
        cls.b = b

    def test_parse(self):
        stems, invariable = self.b.parse(
            "-zuri kv -siyokuwa na hitilafu\nadimu kv -isiyopatikana\n-angu1 kv kimilikishi\n"
            "-enye kv -liyo na\n")
        self.assertEqual(stems["zuri"], "kamusi")
        self.assertNotIn("angu", stems)
        self.assertNotIn("enye", stems)
        self.assertEqual(stems["kubwa"], "curated")      # merged curated core
        self.assertEqual(invariable, ["adimu"])


if __name__ == "__main__":
    unittest.main()
