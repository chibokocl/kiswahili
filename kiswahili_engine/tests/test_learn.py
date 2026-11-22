"""Tests for learning noun classes from running text."""

import json
import tempfile
import unittest
from pathlib import Path

from kiswahili_engine.core.noun_lexicon import NounLexicon
from kiswahili_engine.learn import clauses, collect_forms, build_model, learn


def model_for(text, min_obs=3):
    forms, signals = collect_forms([text])
    return build_model(forms, signals, min_obs)


class TestLearner(unittest.TestCase):
    def test_distinctive_class_is_learned(self):
        text = "kitabu cha mtoto. kitabu kizuri. kitabu hiki kimeanguka. kitabu changu. " * 2
        got = model_for(text)["kitabu"]
        self.assertEqual([p for p, _, _ in got[1]], ["7/8"])

    def test_pair_evidence_resolves_ya_ambiguity(self):
        # 'ya' alone fits 3/4, 5/6 and 9/10; adding 'za' only 9/10 explains
        text = "nyumba ya mtoto. nyumba ya baba. nyumba za watu. nyumba nzuri. " * 2
        got = model_for(text)["nyumba"]
        self.assertEqual(got[1][0][0], "9/10")
        self.assertNotIn("3/4", [p for p, _, _ in got[1]])

    def test_singular_only_evidence_stays_ambiguous(self):
        # wa / wangu fit 1/2, 3/4, 11/10 and 14/6 alike: keep every consistent pair
        text = "mkono wa mtu. mkono wangu. mkono wa kulia. " * 2
        pairs = [p for p, _, _ in model_for(text)["mkono"][1]]
        self.assertIn("1/2", pairs)
        self.assertIn("3/4", pairs)

    def test_number_is_tracked(self):
        text = "vitabu vya mtoto. vitabu vizuri. vitabu hivi. " * 2
        (pair, _, number), = model_for(text)["vitabu"][1]
        self.assertEqual((pair, number), ("7/8", "p"))

    def test_verb_subject_marker_counts_as_weaker_evidence(self):
        text = "kitabu kimeanguka. kitabu kinasomwa. kitabu kilianguka. "
        self.assertNotIn("kitabu", model_for(text))             # 3 x 0.5 < min_obs
        self.assertEqual(model_for(text * 3)["kitabu"][1][0][0], "7/8")

    def test_too_little_evidence_is_dropped(self):
        self.assertNotIn("kitabu", model_for("kitabu cha mtoto. kitabu kizuri."))

    def test_contradictory_evidence_is_dropped(self):
        text = "foo cha mtu. foo vya mtu. foo la mtu. foo za mtu. foo wa mtu. foo ya mtu. "
        self.assertNotIn("foo", model_for(text))

    def test_prepositions_are_not_nouns(self):
        text = "kabla ya kazi. kabla ya siku. kabla ya mwaka. " * 2
        self.assertNotIn("kabla", model_for(text))

    def test_punctuation_digits_and_verse_numbers_break_adjacency(self):
        pairs = {(a, b) for words in clauses("nyumba 5 ya baba. nyumba, ya mtu") for a, b in zip(words, words[1:])}
        self.assertNotIn(("nyumba", "ya"), pairs)
        text = "kitabu 5 cha mtoto. kitabu, kizuri. " * 4
        self.assertNotIn("kitabu", model_for(text))

    def test_learn_round_trip_and_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "c.txt"
            f.write_text("kitabu cha mtoto. kitabu kizuri. kitabu hiki kimeanguka. " * 3, encoding="utf-8")
            out = learn([f], source_note="CC BY-SA test")
        self.assertEqual(out["meta"]["source_note"], "CC BY-SA test")
        self.assertIn("kitabu", out["words"])


class TestLexiconFallback(unittest.TestCase):
    def lexicon(self, learned):
        entries = [{"w": "kitabu", "ngeli": "7/8", "n": "singular", "pl": "vitabu", "inv": False,
                    "proper": False, "variant": False, "anim": None}]
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "learned.json"
            f.write_text(json.dumps({"words": learned}), encoding="utf-8")
            lex = NounLexicon(entries, json.loads(f.read_text())["words"])
        return lex

    def test_learned_words_are_found_when_the_dictionary_lacks_them(self):
        lex = self.lexicon({"nyumba": [900, [["9/10", 0.98, "sp"]]], "vitu": [200, [["7/8", 0.97, "p"]]]})
        self.assertEqual({(e.ngeli, e.number) for e in lex.lookup("nyumba")},
                         {("9/10", "singular"), ("9/10", "plural")})
        self.assertEqual([(e.ngeli, e.number, e.source) for e in lex.lookup("vitu")],
                         [("7/8", "plural", "learned")])

    def test_dictionary_wins_over_learned(self):
        lex = self.lexicon({"kitabu": [100, [["9/10", 0.9, "sp"]]]})
        self.assertEqual([(e.ngeli, e.source) for e in lex.lookup("kitabu")], [("7/8", "headword")])

    def test_learned_is_lower_confidence_than_dictionary(self):
        lex = self.lexicon({"nyumba": [900, [["9/10", 0.98, "sp"]]]})
        self.assertLess(lex.lookup("nyumba")[0].confidence, lex.lookup("kitabu")[0].confidence)

    def test_packaged_model_loads_and_serves(self):
        lex = NounLexicon.load()
        self.assertEqual(lex.best("nyumba").source, "learned")      # the dictionary has no 'nyumba'
        self.assertIn(("9/10", "singular"), lex.candidates("nyumba"))
        self.assertEqual(lex.best("kitabu").source, "headword")
        self.assertEqual(NounLexicon.load(learned=False).lookup("nyumba"), [])


if __name__ == "__main__":
    unittest.main()
