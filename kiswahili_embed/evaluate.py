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

With ``--docs`` (the health documents; see ``documents.py`` for the held-out ones):

``health``          150 hand-written questions (95 caregiver, 55 clinician voice) -> the held-out paragraph(s) that answer them (pool:
                    all ~290 held-out paragraphs, mostly same-topic distractors)
``health+bible``    the same plus 2,000 Bible distractors
``health:caregiver`` / ``health:clinician``  the same split by who is asking
``health-noise``    noisy -> clean held-out health sentences

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
              gold: Sequence, pool_role: str = "query",
              exclude: Sequence[int] = ()) -> Dict[str, float]:
    """``gold[i]`` is the pool index (or a list of indices, any of which counts) for query i;
    ``exclude[i]`` is a pool index that query i may not match (the query sentence itself)."""
    q = emb.encode(queries)
    p = emb.encode(pool, role=pool_role)
    scores = q @ p.T
    if len(exclude):
        scores[np.arange(len(exclude)), exclude] = -np.inf
    ranks = np.empty(len(gold), dtype=np.int64)
    for i, g in enumerate(gold):
        g = [g] if isinstance(g, (int, np.integer)) else list(g)
        mask = np.zeros(scores.shape[1], dtype=bool)
        mask[g] = True
        best = scores[i, mask].max()
        ranks[i] = int((scores[i, ~mask] > best).sum()) + 1
    return {"r@1": float((ranks == 1).mean()), "r@10": float((ranks <= 10).mean()),
            "mrr": float((1.0 / ranks).mean()), "n": len(queries), "pool": len(pool),
            "ranks": ranks.tolist()}


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


def health_task(path: Path, pool: List[str], distractors: List[str], who: str = "") -> tuple:
    """Questions whose answer is any pool paragraph containing one of the ``gold`` phrases.
    ``who`` keeps only questions written in that voice ("caregiver" or "clinician")."""
    items = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    items = [it for it in items if not who or it.get("who") == who]
    gold = [[j for j, para in enumerate(pool) if any(g in para for g in it["gold"])] for it in items]
    missing = [it["query"] for it, g in zip(items, gold) if not g]
    if missing:
        raise ValueError(f"no pool paragraph answers: {missing}")
    return [it["query"] for it in items], pool + distractors, gold, "passage"


def run(model: str, limit: int = 1000, seed: int = 7,
        docs: Sequence[Path] = ()) -> Dict[str, Dict[str, float]]:
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
    if docs:
        from .corpus import dedupe
        from .documents import load_documents, split_documents
        train_docs, test_docs = split_documents(load_documents(docs))
        pool = dedupe([p for d in test_docs for p in d.paragraphs])
        qa = DATA_DIR / "health_search_eval.jsonl"
        tasks["health"] = health_task(qa, pool, [])
        tasks["health+bible"] = health_task(qa, pool, rng.sample(bible_test, 2000))
        tasks["health:caregiver"] = health_task(qa, pool, [], who="caregiver")
        tasks["health:clinician"] = health_task(qa, pool, [], who="clinician")
        test_sents = [s for d in test_docs for s in d.sentences]
        tasks["health-noise"] = noise_task(test_sents, seed, limit)
    return {name: retrieval(emb, *t) for name, t in tasks.items()}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=DEFAULT_BASE)
    ap.add_argument("--limit", type=int, default=1000, help="queries per task")
    ap.add_argument("--json", type=Path, help="also write results here")
    ap.add_argument("--docs", type=Path, nargs="*", default=[],
                    help="modern documents (PDF/txt or folders); enables the health tasks")
    args = ap.parse_args(argv)
    res = run(args.model, args.limit, docs=args.docs)
    print(f"model: {args.model}")
    print(f"{'task':<18}{'r@1':>7}{'r@10':>7}{'mrr':>7}{'n':>6}{'pool':>6}")
    for name, r in res.items():
        print(f"{name:<18}{r['r@1']:>7.3f}{r['r@10']:>7.3f}{r['mrr']:>7.3f}{r['n']:>6}{r['pool']:>6}")
    if args.json:
        args.json.write_text(json.dumps({"model": args.model, "results": res}, indent=2))


if __name__ == "__main__":
    main()
