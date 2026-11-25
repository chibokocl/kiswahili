"""
Kiswahili sentence embeddings and a small semantic-search index.

    from kiswahili_embed import SwahiliEmbedder, SemanticIndex
    emb = SwahiliEmbedder()                       # fine-tuned model if trained, else the base model
    index = SemanticIndex(emb)
    index.add(["Mvua kubwa imenyesha Dar es Salaam.", "Bei ya mahindi imepanda."])
    index.search("hali ya hewa", k=1)             # [(0.83, 0, 'Mvua kubwa ...')]

The model is a multilingual E5 encoder.  E5 expects every input to start with ``"query: "`` or
``"passage: "``; :class:`SwahiliEmbedder` adds it, so callers pass plain text.  Use
``encode(..., role="passage")`` for the documents you search over and the default ``"query"``
for search queries and for symmetric tasks (similarity, clustering).  This matters: on the
hand-written search benchmark, encoding the documents as queries cuts recall@1 from 0.28 to 0.05.
Vectors are L2-normalised, so a dot product is the cosine similarity.
"""

from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union
import json
import os

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = "intfloat/multilingual-e5-small"
DEFAULT_FINETUNED = ROOT / "models" / "kiswahili-e5-small"
PREFIXES = {"query": "query: ", "passage": "passage: ", "none": ""}


def default_model() -> str:
    env = os.environ.get("KISWAHILI_EMBED_MODEL")
    if env:
        return env
    return str(DEFAULT_FINETUNED) if (DEFAULT_FINETUNED / "config.json").exists() else DEFAULT_BASE


class SwahiliEmbedder:
    """Thin wrapper around a sentence-transformers model with the E5 prefix and normalisation."""

    def __init__(self, model: Optional[str] = None, device: str = "cpu", batch_size: int = 64):
        from sentence_transformers import SentenceTransformer   # heavy import: keep it lazy
        self.name = str(model or default_model())
        self.model = SentenceTransformer(self.name, device=device)
        self.batch_size = batch_size
        # Fine-tuned models store the prefixes as sentence-transformers prompts.
        self.uses_prefixes = "e5" in self.name.lower() or bool(getattr(self.model, "prompts", {}).get("query"))

    @property
    def dim(self) -> int:
        get = getattr(self.model, "get_embedding_dimension", None) or \
            self.model.get_sentence_embedding_dimension
        return int(get())

    def encode(self, texts: Union[str, Sequence[str]], role: str = "query") -> np.ndarray:
        prefix = PREFIXES[role] if self.uses_prefixes else ""
        single = isinstance(texts, str)
        items = [texts] if single else list(texts)
        vecs = self.model.encode([prefix + t for t in items], batch_size=self.batch_size,
                                 normalize_embeddings=True, convert_to_numpy=True,
                                 show_progress_bar=False).astype(np.float32)
        return vecs[0] if single else vecs

    def similarity(self, a: str, b: str) -> float:
        va, vb = self.encode([a, b])
        return float(va @ vb)


class SemanticIndex:
    """Exact (brute-force) cosine search; fine up to a few hundred thousand texts."""

    def __init__(self, embedder: Optional[SwahiliEmbedder] = None):
        self.embedder = embedder
        self.texts: List[str] = []
        self.vectors = np.zeros((0, 0), dtype=np.float32)

    def _emb(self) -> SwahiliEmbedder:
        if self.embedder is None:
            self.embedder = SwahiliEmbedder()
        return self.embedder

    def add(self, texts: Sequence[str]) -> None:
        vecs = self._emb().encode(list(texts), role="passage")
        self.vectors = vecs if not self.texts else np.vstack([self.vectors, vecs])
        self.texts.extend(texts)

    def search(self, query: str, k: int = 5) -> List[Tuple[float, int, str]]:
        if not self.texts:
            return []
        scores = self.vectors @ self._emb().encode(query)
        top = np.argsort(-scores)[:k]
        return [(float(scores[i]), int(i), self.texts[i]) for i in top]

    def save(self, path: Union[str, Path]) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        np.save(path / "vectors.npy", self.vectors)
        meta = {"model": self._emb().name, "texts": self.texts}
        (path / "texts.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Union[str, Path], embedder: Optional[SwahiliEmbedder] = None) -> "SemanticIndex":
        path = Path(path)
        meta = json.loads((path / "texts.json").read_text(encoding="utf-8"))
        idx = cls(embedder or SwahiliEmbedder(meta["model"]))
        idx.texts = meta["texts"]
        idx.vectors = np.load(path / "vectors.npy")
        return idx
