# kiswahili_embed: Kiswahili sentence embeddings

A multilingual sentence encoder (`intfloat/multilingual-e5-small`, 118M parameters, 384-dim)
fine-tuned on open Kiswahili text, plus semantic search, benchmarks and export.

```bash
pip install -e ".[embed]"                 # torch, sentence-transformers, datasets, accelerate
python -m kiswahili_embed.corpus          # extract sentences from swahili_corpus/Biblia.pdf (needs pdftotext)
python -m kiswahili_embed.train           # ~20 min on 4 CPU cores -> models/kiswahili-e5-small
python -m kiswahili_embed.evaluate --model models/kiswahili-e5-small
python -m kiswahili_embed.export          # writes the model card; --push user/repo uploads to the Hub
```

```python
from kiswahili_embed import SwahiliEmbedder, SemanticIndex

emb = SwahiliEmbedder()          # models/kiswahili-e5-small if trained, else the base model
index = SemanticIndex(emb)       # (or set KISWAHILI_EMBED_MODEL to any path / Hub id)
index.add(["Bei ya mahindi imepanda sokoni.", "Timu ya taifa imeshinda mechi ya jana."])
index.search("gharama ya chakula", k=1)   # [(0.34, 0, 'Bei ya mahindi imepanda sokoni.')]
index.save("my_index"); SemanticIndex.load("my_index")

emb.encode(["Kitabu kimeanguka."])        # (1, 384) float32, L2-normalised
emb.similarity("Kitabu kimeanguka.", "Kitabu umeanguka.")   # 0.83
```

E5 models need `query: ` / `passage: ` prefixes; the embedder adds them (`encode(texts,
role="query"|"passage")`). **Encode searched documents as passages**: on the search benchmark,
encoding them as queries drops base-model recall@1 from 0.28 to 0.05.

## How it is trained

No labelled Kiswahili similarity data exists in the repository, so `pairs.py` builds
self-supervised pairs from the train split of the Bible (30.6k sentences, held-out blocks kept
apart), trained with in-batch negatives (MultipleNegativesRankingLoss, batch 64, 1 epoch, lr 2e-5):

| pairs | anchor -> positive | count |
|---|---|---|
| crop | 20-50% span of a sentence -> the sentence | 4,800 |
| neighbour | sentence -> next sentence | 4,800 |
| noise | sentence with typos / wrong concord prefix / dropped words -> clean sentence | 2,400 |

## Results

`python -m kiswahili_embed.evaluate`: recall@1 / MRR, retrieving the right text from a pool.

| task | pool | base r@1 | tuned r@1 | base MRR | tuned MRR |
|---|---|---|---|---|---|
| bible-noise (30% of words corrupted) | 3,224 | 0.982 | 0.990 | 0.988 | 0.994 |
| bible-next (held-out) | 3,224 | 0.032 | 0.043 | 0.059 | 0.084 |
| azimio-noise (unseen modern prose) | 177 | 0.994 | 0.989 | 0.997 | 0.994 |
| azimio-next | 177 | 0.051 | 0.097 | 0.109 | 0.158 |
| **search** (40 modern questions + 2,000 Bible distractors) | 2,040 | 0.225 | **0.400** | 0.289 | **0.466** |
| **search-clean** (same 40, no distractors) | 40 | **0.700** | 0.625 | **0.774** | 0.761 |

For reference, base models on `search`: e5-base 0.300, LaBSE 0.425 (r@1).

**Reading these honestly**

* The gain on `search` is real but comes from telling Bible-style text apart from modern text, so
  modern queries stop matching Bible distractors. On `search-clean` the tuned model is not better
  than the base (3 of 40 queries worse; with 40 items that is within noise). Fine-tuning on one
  Bible translation did **not** improve modern Kiswahili semantics.
* Next-sentence retrieval roughly doubles on unseen prose (azimio-next 0.05 -> 0.10), a sign of
  better topical similarity, but absolute numbers are low.
* Noise robustness was already ~98% in the base model; there is little left to gain there.
* `search_eval.jsonl` was written for this project and has not been checked by a native-speaker
  panel. Treat it as a smoke test, and grow it before trusting small differences.

## Noun classes from embeddings (checker experiment)

`python -m kiswahili_embed.noun_classes` guesses the ngeli of a word from its nearest known nouns
(k=10). On 2,000 held-out dictionary headwords:

| method | accuracy |
|---|---|
| majority class (9/10) | 0.356 |
| longest-prefix rule | 0.648 |
| base-model kNN | 0.653 |
| tuned-model kNN | 0.639 |
| base kNN, only when >=80% of the vote agrees (20% of words) | 0.869 |

The embeddings do not beat a prefix rule, so this is **not** wired into the precision-first
`Checker`. It is kept as a tool and a baseline for future models.

## Licence

The fine-tuned weights derive from the Biblica Open Kiswahili Contemporary Version (CC BY-SA 4.0)
and are released under CC BY-SA 4.0 with the attribution in the model card (`export.py`). The
dictionary (*Kamusi Teule*, all rights reserved) is **not** used for training. The Arusha
Declaration text is used for evaluation only. See `../DATA_LICENSES.md`.

## Next steps

* Modern open text (Swahili Wikipedia, CC BY-SA) and mined pairs (title -> body, question -> answer);
  this is what `search-clean` needs.
* A larger base (LaBSE or e5-base) on a GPU: `--base sentence-transformers/LaBSE`.
* A larger, native-speaker-checked search set.
