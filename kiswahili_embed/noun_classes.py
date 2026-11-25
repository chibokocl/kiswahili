"""
Guess the noun class (ngeli) of a word the lexicon does not know, from its embedding.

Each known singular noun is embedded on its own; an unknown word gets the classes of its nearest
neighbours, weighted by similarity.  The embedding carries both form (*kitabu* is close to other
*ki-* words) and meaning (animals cluster, and animals are mostly 9/10 or 1/2 whatever their
prefix), which a prefix rule cannot see.

    python -m kiswahili_embed.noun_classes          # held-out accuracy vs a prefix baseline

The labels come from ``kiswahili_engine/data/noun_lexicon.json`` (dictionary-derived, development
use only; see ``DATA_LICENSES.md``).  They are used at run time as a lookup table only; they are
not part of the trained model.
"""

from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
import argparse
import json
import random

import numpy as np

from .embedder import SwahiliEmbedder

ROOT = Path(__file__).resolve().parent.parent
NOUN_LEXICON = ROOT / "kiswahili_engine" / "data" / "noun_lexicon.json"


def labelled_nouns(path: Path = NOUN_LEXICON) -> List[Tuple[str, str]]:
    """(headword, ngeli) for singular, non-proper, unambiguous single-word headwords."""
    data = json.loads(path.read_text(encoding="utf-8"))
    by_word: Dict[str, set] = defaultdict(set)
    for w, ngeli, number, _pl, _inv, proper, variant, _anim in data["entries"]:
        if number == "singular" and not proper and not variant and w.isalpha() and len(w) > 2:
            by_word[w].add(ngeli)
    return sorted((w, next(iter(c))) for w, c in by_word.items() if len(c) == 1)


class PrefixBaseline:
    """Majority class of the longest known word-initial string (1-3 letters)."""

    def __init__(self, items: Sequence[Tuple[str, str]]):
        self.table: Dict[str, Counter] = defaultdict(Counter)
        for w, c in items:
            for n in (1, 2, 3):
                self.table[w[:n]][c] += 1
        self.default = Counter(c for _, c in items).most_common(1)[0][0]

    def predict(self, word: str) -> str:
        for n in (3, 2, 1):
            if word[:n] in self.table:
                return self.table[word[:n]].most_common(1)[0][0]
        return self.default


class NounClassGuesser:
    def __init__(self, embedder: Optional[SwahiliEmbedder] = None,
                 items: Optional[Sequence[Tuple[str, str]]] = None, k: int = 10):
        self.embedder = embedder or SwahiliEmbedder()
        items = list(items if items is not None else labelled_nouns())
        self.words = [w for w, _ in items]
        self.labels = [c for _, c in items]
        self.vectors = self.embedder.encode(self.words)
        self.k = k

    def scores(self, words: Sequence[str]) -> List[Dict[str, float]]:
        """Class -> share of neighbour similarity, for each word (shares sum to 1)."""
        sims = self.embedder.encode(list(words)) @ self.vectors.T
        out = []
        for row in sims:
            top = np.argpartition(-row, self.k)[: self.k]
            votes: Dict[str, float] = defaultdict(float)
            for i in top:
                votes[self.labels[i]] += max(float(row[i]), 0.0)
            total = sum(votes.values()) or 1.0
            out.append({c: v / total for c, v in sorted(votes.items(), key=lambda x: -x[1])})
        return out

    def guess(self, word: str) -> Tuple[str, float]:
        """Most likely ngeli and its share of the neighbour vote."""
        best = self.scores([word.lower()])[0]
        c = next(iter(best))
        return c, best[c]


def evaluate(model: Optional[str] = None, test_frac: float = 0.2, seed: int = 3,
             limit: int = 2000) -> Dict[str, float]:
    items = labelled_nouns()
    rng = random.Random(seed)
    rng.shuffle(items)
    n_test = min(limit, int(len(items) * test_frac))
    test, train = items[:n_test], items[n_test:]
    base = PrefixBaseline(train)
    guesser = NounClassGuesser(SwahiliEmbedder(model), train)
    scored = guesser.scores([w for w, _ in test])
    knn = [next(iter(s)) for s in scored]
    conf = [s[p] for s, p in zip(scored, knn)]
    gold = [c for _, c in test]
    pref = [base.predict(w) for w, _ in test]
    confident = [i for i, c in enumerate(conf) if c >= 0.8]
    return {
        "test_words": len(test),
        "majority": float(np.mean([g == base.default for g in gold])),
        "prefix_baseline": float(np.mean([p == g for p, g in zip(pref, gold)])),
        "embedding_knn": float(np.mean([p == g for p, g in zip(knn, gold)])),
        "knn_when_vote>=0.8": float(np.mean([knn[i] == gold[i] for i in confident])) if confident else 0.0,
        "share_vote>=0.8": len(confident) / len(test),
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model")
    args = ap.parse_args(argv)
    for k, v in evaluate(args.model).items():
        print(f"{k:<20} {v:.3f}" if isinstance(v, float) else f"{k:<20} {v}")


if __name__ == "__main__":
    main()
