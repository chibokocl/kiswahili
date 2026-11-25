"""
Retrieval benchmarks for Kiswahili sentence embeddings.

    python -m kiswahili_embed.evaluate                                   # base model
    python -m kiswahili_embed.evaluate --model models/kiswahili-e5-small  # fine-tuned

Every task is "find the right text among many": each query is scored against every candidate,
and we report recall@1, recall@10 and mean reciprocal rank.

``bible-noise``     held-out Bible sentences with heavy noise (30% of words typo'd/re-prefixed/dropped) -> the clean sentence (pool 3.2k)
``bible-next``      held-out sentence -> the sentence after it (pool 3.2k).  Topical, much harder.
``azimio-noise``    the same as bible-noise on the Arusha Declaration: modern political prose the
                    model never trained on (pool ~180)
``azimio-next``     the same as bible-next on the Arusha Declaration
``search``          40 hand-written modern questions (health, weather, money, school ...) -> the
                    passage that answers them, with little word overlap; the pool also holds 2k
                    Bible sentences as distractors.  This checks that Bible fine-tuning has not
                    destroyed general semantics.  Written for this project, not validated by
                    a panel of native speakers: treat it as a smoke test.
``search-clean``    the same 40 questions against only the 40 passages: semantic matching with no
                    out-of-domain distractors.  Compare it with ``search`` to see whether a gain
                    comes from better meaning or only from telling Bible text apart from modern text.

The noise and next-sentence tasks come from the same generator as the training pairs, so they
measure what the training optimised; ``search`` and the Azimio tasks are the honest checks.
"""

from pathlib import Path
from typing import Dict, List, Sequence
import argparse
import json
import random

import numpy as np

from .corpus import DATA_DIR, azimio_sentences, bible_sentences, split
from .embedder import DEFAULT_BASE, SwahiliEmbedder
from .pairs import add_noise


def retrieval(emb: SwahiliEmbedder, queries: Sequence[str], pool: Sequence[str],
              gold: Sequence[int], pool_role: str = "query",
              exclude: Sequence[int] = ()) -> Dict[str, float]:
    """``exclude[i]`` is a pool index that query i may not match (the query sentence itself)."""
    q = emb.encode(queries)
    p = emb.encode(pool, role=pool_role)
    scores = q @ p.T
    if len(exclude):
        scores[np.arange(len(exclude)), exclude] = -np.inf
    gold_scores = scores[np.arange(len(gold)), gold]
    ranks = (scores > gold_scores[:, None]).sum(axis=1) + 1
    return {"r@1": float((ranks == 1).mean()), "r@10": float((ranks <= 10).mean()),
            "mrr": float((1.0 / ranks).mean()), "n": len(queries), "pool": len(pool)}


def noise_task(sents: List[str], seed: int, limit: int) -> tuple:
    rng = random.Random(seed)
    idx = rng.sample(range(len(sents)), min(limit, len(sents)))
    return [add_noise(sents[i], rng, rate=0.3) for i in idx], sents, idx


def next_task(sents: List[str], seed: int, limit: int) -> tuple:
    rng = random.Random(seed)
    idx = rng.sample(range(len(sents) - 1), min(limit, len(sents) - 1))
    return [sents[i] for i in idx], sents, [i + 1 for i in idx], "passage", idx


def search_task(path: Path, distractors: List[str]) -> tuple:
    items = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    pool = [it["passage"] for it in items] + distractors
    return [it["query"] for it in items], pool, list(range(len(items))), "passage"


def run(model: str, limit: int = 1000, seed: int = 7) -> Dict[str, Dict[str, float]]:
    emb = SwahiliEmbedder(model)
    _, bible_test = split(bible_sentences())
    azimio = azimio_sentences()
    rng = random.Random(seed)
    tasks = {
        "bible-noise": noise_task(bible_test, seed, limit),
        "bible-next": next_task(bible_test, seed, limit),
        "azimio-noise": noise_task(azimio, seed, limit),
        "azimio-next": next_task(azimio, seed, limit),
        "search": search_task(DATA_DIR / "search_eval.jsonl", rng.sample(bible_test, 2000)),
        "search-clean": search_task(DATA_DIR / "search_eval.jsonl", []),
    }
    return {name: retrieval(emb, *t) for name, t in tasks.items()}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=DEFAULT_BASE)
    ap.add_argument("--limit", type=int, default=1000, help="queries per task")
    ap.add_argument("--json", type=Path, help="also write results here")
    args = ap.parse_args(argv)
    res = run(args.model, args.limit)
    print(f"model: {args.model}")
    print(f"{'task':<14}{'r@1':>7}{'r@10':>7}{'mrr':>7}{'n':>6}{'pool':>6}")
    for name, r in res.items():
        print(f"{name:<14}{r['r@1']:>7.3f}{r['r@10']:>7.3f}{r['mrr']:>7.3f}{r['n']:>6}{r['pool']:>6}")
    if args.json:
        args.json.write_text(json.dumps({"model": args.model, "results": res}, indent=2))


if __name__ == "__main__":
    main()
