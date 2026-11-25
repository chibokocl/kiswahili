# Data provenance and licences

The code and the data files shipped under `kiswahili_engine/data/` have different origins.
**This is a development record, not legal advice. Review it before publishing the package.**

| File | Derived from | Licence of the source | Status |
|---|---|---|---|
| `learned_noun_classes.json` | *Neno: Bibilia Takatifu* (Biblica Open Kiswahili Contemporary Version), via `python -m kiswahili_engine.learn` | CC BY-SA 4.0, (c) 1984, 1989, 2009, 2015 Biblica, Inc. Attribution + share-alike; the Biblica trademark must not be used on derivatives | Redistributable under CC BY-SA 4.0 with the attribution below. Statistics only; no text is stored |
| `noun_lexicon.json`, `verb_lexicon.json`, `adjective_lexicon.json` | *Kamusi Teule ya Kiswahili*, 3rd ed. (East African Educational Publishers) | "Haki zote zimehifadhiwa": all rights reserved | **Not cleared for redistribution.** Development use only until permission is obtained or the lexicons are rebuilt from open sources. Only headwords, classes, plurals, transitivity, attested extensions and an animacy flag are stored, not definitions, but this does not settle the question |
| `adjective_lexicon.json` (curated stems) | written by hand for this project | project licence | OK |
| `models/kiswahili-e5-small` (not in git; built by `python -m kiswahili_embed.train`) | `intfloat/multilingual-e5-small` (MIT) fine-tuned on sentences of the Biblica text above | CC BY-SA 4.0 (share-alike applies to the fine-tuned weights) | Redistributable under CC BY-SA 4.0 with the Biblica attribution, without the Biblica trademark. Only the Bible is used for training; the dictionary is not |
| `kiswahili_embed/data/search_eval.jsonl` | 40 question/passage pairs written for this project | project licence | OK. Evaluation only |
| `swahili_corpus/azimio.text` in `kiswahili_embed` | Arusha Declaration text | unknown | Evaluation only; never used for training |
| `swahili_corpus/` (word list, PDFs) | Bible PDF above, the dictionary PDF, and a text of the Arusha Declaration | see above / unknown | Not part of the package; spelling uses `swahili_corpus.json`, which mixes these sources |

## Attribution required for `learned_noun_classes.json`

Statistics derived from *Biblica(R) Open Kiswahili Contemporary Version* (Neno: Bibilia Takatifu),
(c) 1984, 1989, 2009, 2015 Biblica, Inc. The original work is available for free at
www.biblica.com and open.bible, under CC BY-SA 4.0
(https://creativecommons.org/licenses/by-sa/4.0). Changes: word-level counts of agreement
patterns were computed from the text; no text is reproduced.

## Plan

Rebuild every lexicon from openly licensed sources (Bible + Swahili Wikipedia, both CC BY-SA),
ship the data as a separate package under CC BY-SA, and keep the code under its own licence.
