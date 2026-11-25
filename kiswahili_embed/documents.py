"""
Modern Kiswahili documents (guides, manuals, leaflets) as training and evaluation text.

``pdftotext`` output of such documents is mostly short lines, bullets, form fields ("Jina la
Mtoto ____", "Ndiyo ☐ Hapana ☐") and occasional broken font encodings ("yĂŶĂƟrirka").
:func:`read_document` repairs ligatures (``ﬁ``, ``Į`` -> fi, ``Ɵ`` -> ti), drops form furniture
and garbled lines, and returns paragraphs; :func:`doc_sentences` splits them into sentences.

Documents are grouped so that near-duplicates (two editions of one card, a chart and its booklet)
stay on the same side of a train/test split: see :data:`HOLDOUT_GROUPS` and :func:`load_documents`.

    python -m kiswahili_embed.documents DIR_OR_PDFS...        # stats per document
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
import argparse
import re
import unicodedata

from .corpus import read_pdf, dedupe

# Characters that only appear when pdftotext could not decode a font (Caesar-shifted glyphs).
GARBLED = re.compile(r"[ĂŶďƵƐŵŝĞůƌĚĐŚŬǀŽƚƉƌɑ\x00-\x08\x0b-\x1f¿]")
FORM = re.compile(r"_{3,}|\.{4,}|☐|□|√")
BULLET = re.compile(r"\s*[•·▪●◦]\s*|(?:^|\n)\s*[A-Z]\s*(?=\n)")
SENT_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z“\"(])")
WORDS = re.compile(r"[A-Za-z']+")

# Ligatures and look-alikes that NFKC does not fix in these PDFs.
REPAIRS = {"Ɵ": "ti", "Į": "fi", "ƞ": "tt", "ﬀ": "ff", "­": ""}


@dataclass
class Document:
    name: str
    paragraphs: List[str]

    @property
    def sentences(self) -> List[str]:
        return doc_sentences(self.paragraphs)


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    for a, b in REPAIRS.items():
        text = text.replace(a, b)
    return text.replace("’", "'").replace("‘", "'")


def swahili_ratio(s: str) -> float:
    """Share of characters that are ASCII letters or spaces (numbers/tables score low)."""
    return sum(ch.isascii() and (ch.isalpha() or ch == " ") for ch in s) / max(1, len(s))


def clean_paragraphs(raw: str, min_words: int = 4) -> List[str]:
    text = normalise(raw)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)                # hyphenated line breaks
    lines = []
    for line in text.splitlines():
        if GARBLED.search(line):
            lines.append("")
            continue
        line = FORM.sub(" ", line).strip()
        lines.append(line)
    text = "\n".join(lines)
    text = BULLET.sub("\n\n", text)                            # bullets start new paragraphs
    text = re.sub(r"(?<=\s)D\s+(?=[A-Z])", "\n\n", text)        # 'D' rendered for a bullet glyph
    out = []
    for para in re.split(r"\n\s*\n", text):
        para = " ".join(para.split())
        para = re.sub(r"^D\s+(?=[A-Z])", "", para)              # 'D' rendered for a bullet glyph
        para = re.sub(r"\s+\d{1,3}\.?$", "", para)               # trailing page/item numbers
        if len(WORDS.findall(para)) >= min_words and swahili_ratio(para) >= 0.8 \
                and "©" not in para and "http" not in para:
            out.append(para)
    return dedupe(out)


def doc_sentences(paragraphs: Iterable[str], min_words: int = 4, max_words: int = 60) -> List[str]:
    out = []
    for para in paragraphs:
        for s in SENT_END.split(para):
            s = s.strip()
            if min_words <= len(s.split()) <= max_words:
                out.append(s)
    return dedupe(out)


def read_document(path: Path) -> Document:
    raw = read_pdf(path) if path.suffix.lower() == ".pdf" else path.read_text("utf-8", errors="ignore")
    return Document(path.stem, clean_paragraphs(raw))


def expand(paths: Sequence[Path]) -> List[Path]:
    out: List[Path] = []
    for p in paths:
        out.extend(sorted(p.glob("*.pdf")) + sorted(p.glob("*.txt")) if p.is_dir() else [p])
    return out


# Substrings of file names; documents matching one group are held out together.
HOLDOUT_GROUPS = [("IYCF",), ("Matibabu",)]


def load_documents(paths: Sequence[Path]) -> List[Document]:
    return [read_document(p) for p in expand(paths)]


def split_documents(docs: Sequence[Document], holdout=HOLDOUT_GROUPS):
    """(train, test) by whole document; a document is test if its name matches a holdout group."""
    keys = [k for group in holdout for k in group]
    test = [d for d in docs if any(k.lower() in d.name.lower() for k in keys)]
    train = [d for d in docs if d not in test]
    return train, test


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", type=Path)
    args = ap.parse_args(argv)
    docs = load_documents(args.paths)
    train, test = split_documents(docs)
    for d in docs:
        side = "test " if d in test else "train"
        print(f"{side} {len(d.paragraphs):>5} paras {len(d.sentences):>5} sents "
              f"{sum(len(s.split()) for s in d.sentences):>6} words  {d.name}")


if __name__ == "__main__":
    main()
