"""
Self-supervised training pairs for contrastive fine-tuning.

There is no labelled Kiswahili similarity data in the repository, so pairs are made from
running text.  Each pair is (anchor, positive); the other positives in a batch serve as negatives
(MultipleNegativesRankingLoss).

``noise``      a sentence with typos, dropped words or a wrong concord prefix -> the clean sentence.
               Teaches robustness to the errors the checker sees (search still works on misspelt
               queries; a misspelt sentence lands next to its correction).
``crop``       a short span of a long sentence (the "query") -> the whole sentence (the "passage").
``neighbour``  a sentence -> the next sentence in the same passage (topical similarity).

E5 models mark inputs as ``query:`` or ``passage:``.  Noise pairs are symmetric (query/query);
crop and neighbour pairs are asymmetric (query/passage), like a search query and a document.
"""

from dataclasses import dataclass
from typing import List, Sequence, Tuple
import random

VOWELS = "aeiou"
CONSONANTS = "bcdfghjklmnprstvwyz"
# Concord prefixes that are commonly confused; swapping one for another makes an agreement error.
CONCORD_PREFIXES = ["ki", "vi", "wa", "ya", "zi", "li", "u", "i", "a", "m", "mi", "ku", "pa"]


@dataclass
class Pair:
    anchor: str
    positive: str
    kind: str


def typo(word: str, rng: random.Random) -> str:
    if len(word) < 3:
        return word
    i = rng.randrange(1, len(word))
    op = rng.random()
    if op < 0.3:                                    # deletion
        return word[:i] + word[i + 1:]
    if op < 0.55:                                   # transposition
        if i >= len(word) - 1:
            i = len(word) - 2
        return word[:i] + word[i + 1] + word[i] + word[i + 2:]
    if op < 0.8:                                    # substitution, same letter type
        pool = VOWELS if word[i].lower() in VOWELS else CONSONANTS
        return word[:i] + rng.choice(pool) + word[i + 1:]
    return word[:i] + word[i - 1] + word[i:]        # doubled letter


def wrong_concord(word: str, rng: random.Random) -> str:
    for p in sorted(CONCORD_PREFIXES, key=len, reverse=True):
        if word.lower().startswith(p) and len(word) > len(p) + 3:
            other = rng.choice([q for q in CONCORD_PREFIXES if q != p])
            return (other.capitalize() if word[0].isupper() else other) + word[len(p):]
    return word


def add_noise(sentence: str, rng: random.Random, rate: float = 0.15) -> str:
    words = sentence.split()
    out: List[str] = []
    for w in words:
        r = rng.random()
        if r < rate:
            out.append(typo(w, rng))
        elif r < rate * 1.4:
            out.append(wrong_concord(w, rng))
        elif r < rate * 1.7 and len(words) > 6:
            continue                                 # drop the word
        else:
            out.append(w)
    if out == words:                                 # nothing changed: force one typo
        long = [i for i, w in enumerate(words) if len(w) >= 3] or [0]
        i = rng.choice(long)
        out = words[:i] + [typo(words[i], rng)] + words[i + 1:]
    return " ".join(out)


def crop(sentence: str, rng: random.Random, min_frac: float = 0.2, max_frac: float = 0.5) -> str:
    words = sentence.split()
    n = max(3, int(len(words) * rng.uniform(min_frac, max_frac)))
    start = rng.randrange(0, max(1, len(words) - n + 1))
    return " ".join(words[start:start + n])


def make_pairs(sentences: Sequence[str], n_noise: int = 3000, n_crop: int = 6000,
               n_neighbour: int = 6000, seed: int = 13) -> List[Pair]:
    """``sentences`` must keep their running order (neighbour pairs use adjacency)."""
    rng = random.Random(seed)
    idx = list(range(len(sentences)))
    pairs: List[Pair] = []
    for i in rng.sample(idx, min(n_noise, len(idx))):
        s = sentences[i]
        pairs.append(Pair(add_noise(s, rng), s, "noise"))
    long_idx = [i for i in idx if len(sentences[i].split()) >= 12]
    for i in rng.sample(long_idx, min(n_crop, len(long_idx))):
        s = sentences[i]
        pairs.append(Pair(crop(s, rng), s, "crop"))
    nb_idx = idx[:-1]
    for i in rng.sample(nb_idx, min(n_neighbour, len(nb_idx))):
        pairs.append(Pair(sentences[i], sentences[i + 1], "neighbour"))
    rng.shuffle(pairs)
    return pairs


def as_columns(pairs: Sequence[Pair]) -> Tuple[List[str], List[str]]:
    anchors = ["query: " + p.anchor for p in pairs]
    positives = [("query: " if p.kind == "noise" else "passage: ") + p.positive for p in pairs]
    return anchors, positives


def make_doc_pairs(docs, n_noise: int = 1000, crops_per_sentence: int = 1,
                   seed: int = 17) -> List[Pair]:
    """Pairs from modern documents (:class:`~kiswahili_embed.documents.Document`).

    ``section``    a sentence -> the paragraph it comes from (when the paragraph is longer), which
                   is the shape of a search hit; plus all the sentence-level kinds above.
    """
    from .documents import doc_sentences
    rng = random.Random(seed)
    out: List[Pair] = []
    sents_all: List[str] = []
    for d in docs:
        for para in d.paragraphs:
            sents = doc_sentences([para])
            sents_all.extend(sents)
            if len(sents) > 1:
                for s in sents:
                    out.append(Pair(s, para, "section"))
        sents = d.sentences
        for i in range(len(sents) - 1):
            out.append(Pair(sents[i], sents[i + 1], "neighbour"))
    for s in sents_all:
        if len(s.split()) >= 8:
            for _ in range(crops_per_sentence):
                out.append(Pair(crop(s, rng, 0.3, 0.6), s, "crop"))
    for s in rng.sample(sents_all, min(n_noise, len(sents_all))):
        out.append(Pair(add_noise(s, rng), s, "noise"))
    rng.shuffle(out)
    return out
