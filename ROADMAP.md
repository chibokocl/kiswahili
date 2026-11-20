# Roadmap: a Kiswahili Grammarly

North star: paste Kiswahili text, get a short list of **flagged issues with spans, plain
explanations and one-click fixes** -- and almost never a flag on correct Kiswahili. A
writing assistant lives or dies on false alarms, so every step is judged by precision first.

## Where we are

| Layer | Status |
|---|---|
| Verb morphology (`VerbParser`) | Slot parser + 3.7k dictionary roots with attested extensions. Recovers the dictionary-attested root for 78% of derived forms (86% give a dictionary-licensed analysis). |
| Noun lexicon (`NounLexicon`) | 13k headwords with ngeli and plurals. Covers ~1/3 of tokens in a sample text. |
| Adjective concord (`ConcordLexicon`) | 61 adjective stems (dictionary + curated) and generated class forms for adjectives, possessives, *-a*, *-ote*. |
| Checker (`Checker`) | `AGR-SV`, `AGR-NA`, `SPELL`, `CAP` with spans, bilingual messages, fixes. |
| Try it | `python -m kiswahili_engine.server` -> one-page browser tester. |
| Evaluation (`tools/evaluate_checker.py`) | Clean-text false alarms + synthetic detection/fix accuracy. |

### Numbers (run `python tools/evaluate_checker.py`)

* **Clean text** (Arusha Declaration, 5.3k words): 0 agreement (verb or adjective) / capitalisation false alarms,
  1.9 spelling flags per 1000 words (some may be genuine typos in the source). That text is
  also part of the spelling corpus, so the spelling figure is optimistic.
* **Synthetic errors** are built from the same lexicons the checker uses, so they only prove the
  logic works end to end (verb agreement: 100% detected and fixed; adjective concord: 87% detected, 100% of those fixed; single-edit typos: ~81% flagged,
  top-3 suggestion contains the right word ~92% of the time). **They are not a measure of real-world
  quality.**

## Next, in priority order

1. **Real error data.** Collect/annotate real mistakes (learner writing, news copy edits) and
   real clean text that is *not* in the spelling corpus. Until then true precision and recall
   are unknown. Every item below should land with cases in this set.
2. **More precise rules** (each needs a lexicon, so extract from the dictionary like nouns/verbs):
   * **animacy**: `*kitabu mzuri` / `*kitabu wa mtoto` are not flagged today because `kijana mzuri`
     (7/8, human) is correct and the lexicon doesn't know which nouns are animate. Deriving an
     animacy flag from the dictionary definitions (mtu, mnyama, ndege ...) would unlock the most
     common concord errors;
   * demonstrative concord (`*kitabu huyu`), non-adjacent modifiers, more adjective stems;
   * tense/negation form errors (`*sipendi`, `*hakupenda` confusions), missing `ku-` on
     monosyllabic verbs (`*anakla`), subject-pronoun / verb-marker mismatch (`*Mimi unasoma`);
   * subject finding beyond "sentence-initial noun + verb" (modifiers, coordinated subjects).
3. **Spelling quality.** The word list is mixed Bible + dictionary text with ~55k one-off tokens
   and dictionary markup (`nm`, `kt`). Replace it with a clean, modern, frequency-weighted
   corpus; add a keyboard/phonetic error model and proper-noun handling.
4. **Standard Kiswahili as default.** The engine's ngeli tables come from a Ki-Micheweni study;
   a general tool needs standard Kiswahili as the default and dialects as options.
5. **Style and clarity** (the other half of Grammarly): sentence length, calques, register.
6. **Delivery**: JSON API, editor/browser integration, latency budget (first call currently loads
   ~90k words and two lexicons).
7. **Translation.** The dictionary is Swahili-to-Swahili; a bilingual lexicon (and a decision on
   rule-based vs model-assisted translation) is needed before translation features.

## Known limits

* Verb parser: no reversive/positional extensions, reduplication, `amba-` relatives, `-ile` perfect.
* Noun lexicon: dictionary omissions (e.g. `nyumba`), ~130 entries lost to PDF column layout.
* Agreement rule only checks `<sentence-initial noun> <verb>`; it will miss most real errors by design.
