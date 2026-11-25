"""
Fine-tune a multilingual sentence encoder on Kiswahili.

    python -m kiswahili_embed.train                        # 12k pairs, 1 epoch: about 1-2 hours on 4 CPU cores
    python -m kiswahili_embed.train --pairs 3000 --epochs 1 -o /tmp/quick   # smoke run

Training data is the train split of the Bible sentences only (CC BY-SA 4.0; see
``DATA_LICENSES.md``); held-out blocks and the Arusha Declaration are kept for
``python -m kiswahili_embed.evaluate``.  The loss is MultipleNegativesRankingLoss (in-batch
negatives), so larger batches give harder negatives; 64 fits comfortably in 16 GB of RAM.
"""

from pathlib import Path
import argparse
import json
import random
import time

from .corpus import bible_sentences, fingerprint, split
from .embedder import DEFAULT_BASE, DEFAULT_FINETUNED
from .pairs import as_columns, make_pairs


def train(base: str, out: Path, n_pairs: int, epochs: int, batch_size: int, lr: float,
          max_len: int, seed: int, docs=(), doc_repeats: int = 1) -> dict:
    import torch
    from datasets import Dataset
    from sentence_transformers import (SentenceTransformer, SentenceTransformerTrainer,
                                       SentenceTransformerTrainingArguments, losses)
    from sentence_transformers.training_args import BatchSamplers

    torch.manual_seed(seed)
    sents = bible_sentences()
    train_sents, _ = split(sents)
    pairs = make_pairs(train_sents, n_noise=int(n_pairs * 0.2), n_crop=int(n_pairs * 0.4),
                       n_neighbour=int(n_pairs * 0.4), seed=seed)
    doc_info = {}
    if docs:
        from .documents import load_documents, split_documents
        from .pairs import make_doc_pairs
        train_docs, test_docs = split_documents(load_documents(docs))
        for r in range(doc_repeats):
            pairs += make_doc_pairs(train_docs, seed=seed + r)
        random.Random(seed).shuffle(pairs)
        doc_info = {"train_documents": [d.name for d in train_docs],
                    "held_out_documents": [d.name for d in test_docs], "doc_repeats": doc_repeats}
    anchors, positives = as_columns(pairs)
    ds = Dataset.from_dict({"anchor": anchors, "positive": positives})

    model = SentenceTransformer(base, device="cpu")
    model.max_seq_length = max_len
    loss = losses.MultipleNegativesRankingLoss(model)
    args = SentenceTransformerTrainingArguments(
        output_dir=str(out / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        learning_rate=lr,
        warmup_ratio=0.1,
        batch_sampler=BatchSamplers.NO_DUPLICATES,
        logging_steps=10,
        save_strategy="no",
        report_to="none",
        seed=seed,
        use_cpu=True,
        dataloader_drop_last=True,
    )
    t0 = time.time()
    SentenceTransformerTrainer(model=model, args=args, train_dataset=ds, loss=loss).train()
    model.prompts = {"query": "query: ", "passage": "passage: "}
    model.save(str(out))
    info = {
        "base_model": base,
        "pairs": {k: sum(p.kind == k for p in pairs) for k in ("noise", "crop", "neighbour", "section")},
        **doc_info,
        "epochs": epochs, "batch_size": batch_size, "lr": lr, "max_seq_length": max_len,
        "seed": seed, "train_sentences": len(train_sents), "corpus_sha1": fingerprint(sents),
        "seconds": round(time.time() - t0),
    }
    (out / "training_info.json").write_text(json.dumps(info, indent=2))
    return info


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("-o", "--out", type=Path, default=DEFAULT_FINETUNED)
    ap.add_argument("--pairs", type=int, default=12000)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--max-len", type=int, default=96)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--docs", type=Path, nargs="*", default=[],
                    help="modern documents (PDF/txt or folders) to add; held-out ones are skipped")
    ap.add_argument("--doc-repeats", type=int, default=1,
                    help="build document pairs this many times (fresh crops/noise each time)")
    args = ap.parse_args(argv)
    info = train(args.base, args.out, args.pairs, args.epochs, args.batch_size, args.lr,
                 args.max_len, args.seed, args.docs, args.doc_repeats)
    print(json.dumps(info, indent=2))
    print(f"saved to {args.out}")


if __name__ == "__main__":
    main()
