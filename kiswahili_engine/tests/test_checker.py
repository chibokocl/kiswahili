"""Tests for the Kiswahili writing checker (issues with spans and fixes)."""

import unittest

from kiswahili_engine.checker import Checker, apply_suggestions, tokenize


class TestChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chk = Checker()

    def rules(self, text, **kw):
        return [(i.rule, i.text) for i in self.chk.check(text, **kw)]

    # ------------------------------------------------------------ tokenizer
    def test_token_offsets_and_sentences(self):
        text = "Ng'ombe analala. Mtoto anacheza!"
        toks = tokenize(text)
        for t in toks:
            self.assertEqual(text[t.start:t.end], t.text)
        self.assertEqual([t.text for t in toks], ["Ng'ombe", "analala", "Mtoto", "anacheza"])
        self.assertEqual([t.first_in_sentence for t in toks], [True, False, True, False])

    # ------------------------------------------------------------ agreement
    def test_agreement_error_has_span_and_fix(self):
        text = "Kitabu umeanguka."
        (issue,) = [i for i in self.chk.check(text) if i.rule == "AGR-SV"]
        self.assertEqual(text[issue.start:issue.end], "umeanguka")
        self.assertEqual(issue.suggestions[0].text, "kimeanguka")
        self.assertIn("ki-", issue.message)
        self.assertTrue(issue.message_sw)
        self.assertEqual(issue.category, "agreement")

    def test_plural_subject_singular_verb(self):
        issues = self.chk.check("Watoto anacheza mpira.")
        self.assertEqual([i.suggestions[0].text for i in issues if i.rule == "AGR-SV"], ["wanacheza"])

    def test_negative_verb_fix(self):
        issues = self.chk.check("Kitabu hautaanguka.")       # hau- = class 3, kitabu = 7/8
        fixes = [i.suggestions[0].text for i in issues if i.rule == "AGR-SV"]
        self.assertEqual(fixes, ["hakitaanguka"])

    def test_correct_sentences_are_not_flagged(self):
        clean = [
            "Mtoto anakula chakula.",
            "Watoto wanacheza mpira.",
            "Kitabu kimeanguka.",
            "Mti umeanguka.",
            "Miti imeanguka.",
            "Wanafunzi wamesoma vitabu.",
        ]
        for s in clean:
            self.assertEqual(self.rules(s), [], s)

    def test_known_false_alarm_traps(self):
        traps = {
            "animate noun, a- agreement": "Ng'ombe analala.",
            "respect plural": "Mwalimu wamefika.",
            "adverbial noun opens sentence": "Leo anakuja.",
            "locative": "Nyumbani analala.",
            "vocative 2sg": "Mtoto unafanya nini?",
            "demonstrative subject": "Haya yanaweza kuwa.",
            "invariable 9/10 plural": "Dalili zimeanza kuonekana.",
            "first person after noun": "Sisi tutajenga nyumba.",
        }
        for name, s in traps.items():
            self.assertEqual([r for r, _ in self.rules(s) if r == "AGR-SV"], [], name)

    # ------------------------------------------------------------ capitalization
    def test_capitalization(self):
        issues = self.chk.check("mtoto anacheza. Yeye anasoma.")
        caps = [i for i in issues if i.rule == "CAP"]
        self.assertEqual([c.suggestions[0].text for c in caps], ["Mtoto"])

    def test_capitalization_guards(self):
        for s in ["Hii ni (ii) sehemu.", 'Alisema: "mkazo ni muhimu".', "Tazama n.k. mengine."]:
            self.assertEqual([r for r, _ in self.rules(s) if r == "CAP"], [], s)

    # ------------------------------------------------------------ spelling
    def test_misspelling_suggests_correction(self):
        issues = [i for i in self.chk.check("Alikwenda shule kila sikuu.") if i.rule == "SPELL"]
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].text, "sikuu")
        self.assertEqual(issues[0].suggestions[0].text, "siku")

    def test_valid_forms_not_flagged(self):
        ok = [
            "Hatupendi kula.",                       # negative verb
            "Tuhakikishe kwamba wanafunzi wanasoma.",  # subjunctive
            "Nitakupenda daima.",
            "Walimu wametoka mjini.",
            "Juma alikuja na Asha.",                 # names
            "Tulinunua CCM kitabu.",                 # acronym
        ]
        for s in ok:
            self.assertEqual([r for r, _ in self.rules(s) if r == "SPELL"], [], s)

    def test_confidence_filter(self):
        low = self.chk.check("Hii ni xqzvbn.", min_confidence=0.0)
        self.assertTrue(any(i.rule == "SPELL" and i.severity == "info" for i in low))
        self.assertEqual([i for i in self.chk.check("Hii ni xqzvbn.") if i.rule == "SPELL"], [])

    # ------------------------------------------------------------ applying fixes
    def test_apply_suggestions(self):
        text = "kitabu umeanguka. Watoto anacheza."
        fixed = apply_suggestions(text, self.chk.check(text))
        self.assertEqual(fixed, "Kitabu kimeanguka. Watoto wanacheza.")

    def test_issue_serialises(self):
        d = self.chk.check("Kitabu umeanguka.")[0].to_dict()
        self.assertEqual({"start", "end", "text", "rule", "category", "severity", "message",
                          "message_sw", "suggestions", "confidence"}, set(d))


if __name__ == "__main__":
    unittest.main()
