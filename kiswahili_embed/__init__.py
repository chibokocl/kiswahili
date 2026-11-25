"""Kiswahili sentence embeddings: a multilingual E5 encoder fine-tuned on open Kiswahili text."""

from .embedder import SwahiliEmbedder, SemanticIndex, DEFAULT_BASE, DEFAULT_FINETUNED

__all__ = ["SwahiliEmbedder", "SemanticIndex", "DEFAULT_BASE", "DEFAULT_FINETUNED"]
