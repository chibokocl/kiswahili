"""
Package a fine-tuned model for sharing: writes a model card (README.md) with the evaluation
results and licence notes into the model folder, and optionally uploads it to the Hugging Face Hub.

    python -m kiswahili_embed.export                                  # card only
    python -m kiswahili_embed.export --push your-name/kiswahili-e5-small  # needs `huggingface-cli login`

The model is fine-tuned on CC BY-SA 4.0 text, so it is released under CC BY-SA 4.0 with the
Biblica attribution (the base model, intfloat/multilingual-e5-small, is MIT).
"""

from pathlib import Path
import argparse
import json

from .embedder import DEFAULT_FINETUNED
from .evaluate import run

CARD = """---
language: sw
license: cc-by-sa-4.0
library_name: sentence-transformers
pipeline_tag: sentence-similarity
base_model: {base}
tags: [sentence-transformers, feature-extraction, sentence-similarity, kiswahili, swahili]
---

# Kiswahili sentence embeddings ({name})

`{base}` fine-tuned on Kiswahili with self-supervised contrastive pairs (in-batch negatives):
short span -> its sentence, sentence -> next sentence, and noisy sentence (typos, wrong concord
prefixes, dropped words) -> clean sentence.

## Usage

Prefix queries with `query: ` and documents with `passage: ` (use `query: ` on both sides for
symmetric similarity). Skipping the `passage: ` prefix on documents hurts search badly.

```python
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("{repo}")
q = m.encode(["query: dawa ya malaria"], normalize_embeddings=True)
d = m.encode(["passage: Lala ndani ya chandarua ili kuepuka kuumwa na mbu."], normalize_embeddings=True)
print(q @ d.T)
```

## Evaluation

Retrieval among a pool of candidates (`python -m kiswahili_embed.evaluate` in the source repository).
`search` is 40 hand-written modern questions with 2,000 Bible distractors; `search-clean` is the
same questions against only their 40 passages.  Both are a smoke test rather than a validated
benchmark (40 items: one query is 0.025).  The other tasks are built like the training pairs.

| task | base r@1 | fine-tuned r@1 | base MRR | fine-tuned MRR | pool |
|---|---|---|---|---|---|
{rows}

## Training data and licence

Trained only on the train split of *Biblica® Open Kiswahili Contemporary Version (Neno: Bibilia
Takatifu)*, © 1984, 1989, 2009, 2015 Biblica, Inc., CC BY-SA 4.0. The original work by Biblica,
Inc. is available for free at www.biblica.com and open.bible. Changes: sentences were extracted
and turned into training pairs; this model is a derivative work and is released under CC BY-SA 4.0.
It is not endorsed by Biblica.

Training details: `training_info.json`.

## Limitations

The training text is a single Bible translation.  The gain on `search` comes from telling
Bible-style text apart from modern text, not from better modern semantics: on `search-clean` the
fine-tuned model is no better than the base (slightly worse, within the noise of 40 items).  Use
it where Kiswahili text of mixed register is searched together; for modern-only text the base
model is as good.  Modern vocabulary (technology, health, politics) comes from the base model.
"""


def card(model_dir: Path, repo: str) -> str:
    info = json.loads((model_dir / "training_info.json").read_text())
    base_res, ft_res = run(info["base_model"]), run(str(model_dir))
    rows = "\n".join(
        f"| {t} | {base_res[t]['r@1']:.3f} | {ft_res[t]['r@1']:.3f} | {base_res[t]['mrr']:.3f} | "
        f"{ft_res[t]['mrr']:.3f} | {ft_res[t]['pool']} |" for t in ft_res)
    return CARD.format(base=info["base_model"], name=model_dir.name, repo=repo, rows=rows)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", type=Path, default=DEFAULT_FINETUNED)
    ap.add_argument("--push", metavar="REPO_ID", help="upload to this Hugging Face repo")
    args = ap.parse_args(argv)
    repo = args.push or f"<user>/{args.model.name}"
    (args.model / "README.md").write_text(card(args.model, repo), encoding="utf-8")
    print(f"wrote {args.model / 'README.md'}")
    if args.push:
        from huggingface_hub import HfApi
        api = HfApi()
        api.create_repo(args.push, exist_ok=True)
        api.upload_folder(folder_path=str(args.model), repo_id=args.push,
                          ignore_patterns=["checkpoints/*"])
        print(f"uploaded to https://huggingface.co/{args.push}")


if __name__ == "__main__":
    main()
