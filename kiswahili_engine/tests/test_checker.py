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

    def test_inanimate_noun_with_animate_verb_marker(self):
        issues = self.chk.check("Kitabu anasoma.")
        fixes = [i.suggestions[0].text for i in issues if i.rule == "AGR-SV"]
        self.assertEqual(fixes, ["kinasoma"])
        (rel,) = [i for i in issues if i.rule == "AGR-SV"][0].related
        self.assertEqual(rel["role"], "subject")

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
            "animate noun in 7/8, a- agreement": "Kijana anacheza.",
            "animate noun, plural wa- agreement": "Simba wanakuja.",
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

    def test_doubled_letter_typo_ranks_first(self):
        # 'kiu' (thirst) is a rarer word than 'kitu', but dropping a doubled letter is the commonest typo
        (issue,) = [i for i in self.chk.check("Nina kiuu sana.") if i.rule == "SPELL"]
        self.assertEqual(issue.suggestions[0].text, "kiu")
        self.assertNotIn("ki", [s.text for s in issue.suggestions])

    def test_transposition_is_one_cheap_edit(self):
        self.assertEqual(self.chk.suggest("kitabu"), self.chk.suggest("kitabu"))   # cached, stable
        top = [w for w, _ in self.chk.suggest("shuleu", 5)]
        self.assertIn("shule", top)
        self.assertEqual([w for w, _ in self.chk.suggest("kiatbu", 3)][0], "kitabu")

    def test_dictionary_nouns_can_be_suggested(self):
        # 'kiu' is a dictionary noun; suggestions are not limited to corpus words
        self.assertIn("kiu", [w for w, _ in self.chk.suggest("kiuu", 8)])

    def test_unattested_ma_plural_gets_concord_checked(self):
        issues = self.chk.check("Nilinunua masoda za baridi.")
        (issue,) = [i for i in issues if i.rule == "AGR-NA"]
        self.assertEqual(issue.suggestions[0].text, "ya")
        self.assertEqual(issue.related[0]["text"], "masoda")
        self.assertEqual([r for r, _ in self.rules("Nilinunua masoda ya baridi.")], [])

    def test_noun_missing_from_dictionary_uses_prefix_class(self):
        # 'kituo' is not a dictionary headword; ki- gives class 7, so 'ya' must be 'cha'
        text = "Tafadhali fika kituo ya afya karibu nawe."
        (issue,) = [i for i in self.chk.check(text) if i.rule == "AGR-NA"]
        self.assertEqual((issue.text, issue.suggestions[0].text), ("ya", "cha"))
        self.assertEqual(issue.related[0]["text"], "kituo")
        self.assertLess(issue.confidence, 0.85)            # inferred class, so less sure than a lookup
        self.assertEqual(self.rules("Tafadhali fika kituo cha afya karibu nawe."), [])
        self.assertEqual([r for r, _ in self.rules("Vituo vya afya vimefunguliwa.")], [])

    def test_prefix_guess_is_not_used_for_verbs_adverbs_and_locatives(self):
        for s in ["Alifanya kisheria kabisa.", "Wanaishi vijijini.", "Vinginevyo, itakuwa vigumu.",
                  "Kisha ya kwanza ilifika.", "Hii ni kitega uchumi vyao."]:
            self.assertEqual([r for r, _ in self.rules(s) if r.startswith("AGR")], [], s)

    def test_agreement_needs_subject_and_verb_adjacent(self):
        self.assertEqual([r for r, _ in self.rules("Kitabu, kimeanguka.") if r == "AGR-SV"], [])
        self.assertEqual([r for r, _ in self.rules("Vinginevyo, itakuwa vizuri.") if r == "AGR-SV"], [])

    def test_attested_ma_words_are_not_treated_as_plural_nouns(self):
        for s in ["Alifika mapema sana.", "Alikuja mapema kwa kazi."]:
            self.assertEqual([r for r, _ in self.rules(s) if r == "AGR-NA"], [], s)

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

    # ------------------------------------------------------------ prepositions / standard forms
    def test_kwa_before_place_after_motion_verb(self):
        text = "Tafadhali enda kwa kituo cha afya karibu kwako sasa."
        (issue,) = [i for i in self.chk.check(text) if i.rule == "PREP-KWA"]
        self.assertEqual(text[issue.start:issue.end], "kwa kituo")
        # 'kituoni cha afya' would be wrong, so only 'kwenye' is offered before a genitive
        self.assertEqual([s.text for s in issue.suggestions], ["kwenye kituo"])
        issues = self.chk.check("Aliingia kwa shule.")
        (issue,) = [i for i in issues if i.rule == "PREP-KWA"]
        self.assertEqual([s.text for s in issue.suggestions], ["kwenye shule", "shuleni"])

    def test_kwa_with_people_and_things_is_fine(self):
        for s in ["Alikwenda kwa daktari.", "Alienda kwa gari.", "Anakuja kwa mwalimu.",
                  "Nenda kwenye kituo.", "Tafadhali nenda kituoni.", "Alipika kwa moto.",
                  "Nilinunua kwa shilingi mia.", "Kituo kiko karibu kwa shule."]:
            self.assertEqual([r for r, _ in self.rules(s) if r == "PREP-KWA"], [], s)

    def test_standard_imperative(self):
        issues = self.chk.check("Tafadhali enda sasa. Enda nyumbani.")
        self.assertEqual([i.suggestions[0].text for i in issues if i.rule == "STD-IMP"],
                         ["nenda", "Nenda"])
        for s in ["Tafadhali nenda sasa.", "Anaenda sokoni.", "Alikwenda mjini."]:
            self.assertEqual([r for r, _ in self.rules(s) if r == "STD-IMP"], [], s)

    def test_locative_forms_are_valid_words(self):
        for s in ["Alikwenda hospitalini.", "Wanaishi mjini.", "Nenda kituoni.", "Yuko shuleni.",
                  "Alirudi nyumbani."]:
            self.assertEqual([r for r, _ in self.rules(s) if r == "SPELL"], [], s)

    def test_sentences_that_are_fine_stay_silent(self):
        self.assertEqual(self.rules("Mwanamke wangu ana homa."), [])

    # ------------------------------------------------------------ applying fixes
    def test_apply_suggestions(self):
        text = "kitabu umeanguka. Watoto anacheza."
        fixed = apply_suggestions(text, self.chk.check(text))
        self.assertEqual(fixed, "Kitabu kimeanguka. Watoto wanacheza.")

    def test_issue_serialises(self):
        d = self.chk.check("Kitabu umeanguka.")[0].to_dict()
        self.assertEqual({"start", "end", "text", "rule", "category", "severity", "message",
                          "message_sw", "suggestions", "confidence", "related"}, set(d))


if __name__ == "__main__":
    unittest.main()
