"""Tests for the dictionary-derived noun lexicon and its use in the engine."""

import sys
import unittest
from pathlib import Path

from kiswahili_engine import create_engine
from kiswahili_engine.core.ngeli_system import EnhancedNgeliSystem
from kiswahili_engine.core.noun_lexicon import NounLexicon

TOOLS = Path(__file__).resolve().parents[2] / "tools"


class TestNounLexicon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = NounLexicon.load()

    def pair(self, word):
        e = self.lex.best(word)
        return (e.ngeli, e.number) if e else None

    def test_size(self):
        self.assertGreater(len(self.lex), 10000)

    def test_headwords(self):
        self.assertEqual(self.pair("mtoto"), ("1/2", "singular"))
        self.assertEqual(self.pair("mwalimu"), ("1/2", "singular"))
        self.assertEqual(self.pair("kitabu"), ("7/8", "singular"))
        self.assertEqual(self.pair("chakula"), ("7/8", "singular"))   # ch- = ki- before a vowel
        self.assertEqual(self.pair("mpira"), ("3/4", "singular"))
        self.assertEqual(self.pair("ukweli"), ("14/6a", "singular"))
        self.assertEqual(self.pair("jicho"), ("5/6", "singular"))

    def test_plurals(self):
        self.assertEqual(self.pair("watoto"), ("1/2", "plural"))      # explicit
        self.assertEqual(self.pair("macho"), ("5/6", "plural"))       # irregular, explicit
        self.assertEqual(self.pair("vyakula"), ("7/8", "plural"))
        self.assertEqual(self.pair("maji"), ("5/6", "plural"))        # plural-only noun

    def test_derived_plural_is_lower_confidence(self):
        derived = [e for e in self.lex.lookup("miti") if e.source == "plural_rule"]
        explicit = [e for e in self.lex.lookup("watoto") if e.source == "plural"]
        if derived:
            self.assertLess(derived[0].confidence, explicit[0].confidence)

    def test_ambiguous_headword_lists_alternatives(self):
        self.assertIn(("3/4", "singular"), self.lex.candidates("mtoto"))
        self.assertIn(("1/2", "singular"), self.lex.candidates("mtoto"))

    def test_shape_breaks_ties(self):
        # 'kiti' is listed under both 1/2 and 7/8; the ki- shape makes 7/8 win
        self.assertEqual(self.lex.best("kiti").ngeli, "7/8")

    def test_unknown_and_normalisation(self):
        self.assertEqual(self.lex.lookup("zzzzqx"), [])
        self.assertIn("MTOTO", self.lex)
        self.assertNotIn("anakula", self.lex)


class TestEngineUsesLexicon(unittest.TestCase):
    def test_identification(self):
        ns = EnhancedNgeliSystem()
        r = ns.identify_ngeli_enhanced("mtoto")
        self.assertEqual((r.ngeli_class, r.number), ("1/2", "singular"))
        self.assertEqual(r.morphological_analysis["segmentation_method"], "lexicon")
        r = ns.identify_ngeli_enhanced("chakula")
        self.assertEqual(r.ngeli_class, "7/8")

    def test_heuristics_still_work_for_unknown_words(self):
        ns = EnhancedNgeliSystem()
        r = ns.identify_ngeli_enhanced("kijitu")      # derived form, not a headword
        self.assertIsNotNone(r)
        self.assertNotEqual(r.morphological_analysis.get("segmentation_method"), "lexicon")

    def test_lexicon_can_be_disabled(self):
        ns = EnhancedNgeliSystem(use_noun_lexicon=False)
        r = ns.identify_ngeli_enhanced("mtoto")
        self.assertNotEqual((r.morphological_analysis or {}).get("segmentation_method"), "lexicon")

    def test_regression_mtoto_anakula_chakula(self):
        r = create_engine().analyze_sentence_enhanced("Mtoto anakula chakula")
        self.assertTrue(r["agreement"].subject_verb_agreement)
        self.assertEqual(r["agreement"].issues, [])

    def test_mismatch_still_flagged(self):
        ns = EnhancedNgeliSystem()
        self.assertTrue(ns.check_enhanced_agreement("mtoto", "anacheza")["verb_agreement"])
        self.assertFalse(ns.check_enhanced_agreement("mtoto", "wanacheza")["verb_agreement"])
        self.assertFalse(ns.check_enhanced_agreement("kitabu", "anacheza")["verb_agreement"])

    def test_ambiguous_subject_uses_matching_reading(self):
        ns = EnhancedNgeliSystem()
        r = ns.check_enhanced_agreement("mtoto", "umeanguka")   # mtoto as 3/4 'shoot'
        self.assertTrue(r["verb_agreement"])
        self.assertTrue(any("read as ngeli 3/4" in s for s in r["special_cases"]))


class TestBuilderParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(TOOLS))
        import build_noun_lexicon as b
        cls.b = b

    def parse(self, text):
        entries, stats = self.b.parse(text)
        return {(e["w"], e["ngeli"]): e for e in entries}, stats

    def test_basic_and_plural(self):
        got, _ = self.parse("afisa nm (maafisa) |a-/wa-| mtu ambaye\nkitabu nm |ki-/vi-| 1. kurasa\n")
        self.assertEqual(got[("afisa", "1/2")]["pl"], "maafisa")
        self.assertEqual(got[("kitabu", "7/8")]["pl"], None)

    def test_homograph_digit_and_plural_after_nm(self):
        got, _ = self.parse("afu1 nm (maafu) |li-/ya-| ua la mwafu\nafu2 nm (maafu) |li-/ya-| 1. msamaha\n")
        self.assertEqual(list(got), [("afu", "5/6")])

    def test_variants(self):
        got, _ = self.parse("aalimu2 Pia, alimu nm |a-/wa-| mtu mwenye elimu\n")
        self.assertIn(("aalimu", "1/2"), got)
        self.assertTrue(got[("alimu", "1/2")]["variant"])

    def test_phrases_verbs_and_interjections_skipped(self):
        got, stats = self.parse(
            "Agano la Kale nm |li-| sehemu ya Biblia\n"
            "abir.i1 kt -ele- safiri\n"
            "aa!1 ki tamko\n")
        self.assertEqual(got, {})
        self.assertEqual(stats["skipped_phrase"], 1)

    def test_malformed_delimiters_tolerated(self):
        got, _ = self.parse("kuzi2 nm |a-/wa) aina ya\nkiambo nm (viambo) ki-/vi-| kijiji.\n")
        self.assertIn(("kuzi", "1/2"), got)
        self.assertIn(("kiambo", "7/8"), got)

    def test_tag_mapping(self):
        self.assertEqual(self.b.TAG_MAP[self.b.normalise_tag("ya-/ya-")][:2], ("5/6", "plural"))
        self.assertEqual(self.b.normalise_tag("ki-vi-"), ("ki", "vi"))
        self.assertNotIn(self.b.normalise_tag("kd"), self.b.TAG_MAP)   # usage label, not a ngeli


if __name__ == "__main__":
    unittest.main()
