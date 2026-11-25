"""
Clean Kiswahili sentences for training and evaluating the embedding model.

The only text used for *training* is the Biblica Open Kiswahili Contemporary Version
(``swahili_corpus/Biblia.pdf``, CC BY-SA 4.0), because the fine-tuned model is meant to be
exported and the dictionary (*Kamusi Teule*) is all rights reserved.  The Arusha Declaration
(``swahili_corpus/azimio.text``) is used for out-of-domain *evaluation only*.

``pdftotext`` interleaves the verses with cross-references ("16:12 Ay 6:5; 11:12"), footnote
letters, verse numbers and page numbers; :func:`clean_bible` strips those and returns running
text, and :func:`sentences` splits it into sentences.

    python -m kiswahili_embed.corpus            # writes data/bible_sentences.txt and prints stats
"""

from pathlib import Path
from typing import Iterable, List, Tuple
import argparse
import hashlib
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BIBLE_PDF = ROOT / "swahili_corpus" / "Biblia.pdf"
AZIMIO = ROOT / "swahili_corpus" / "azimio.text"
DATA_DIR = Path(__file__).resolve().parent / "data"

# A cross-reference line starts with chapter:verse, e.g. "16:12 Ay 6:5; 11:12; Hos 8:9; Za".
XREF_START = re.compile(r"^\d+:\d+[\s;,]")
# Continuation of a cross-reference list: book abbreviations and numbers only.
XREF_CONT = re.compile(r"^(?:[1-3]?[A-Z][a-z]{0,4}\s*)?[\d:;,\-–\s]+(?:[1-3]?[A-Z][a-z]{0,4})?$")
FOOTNOTE_LETTER = re.compile(r"^[a-z]{1,2}$")
NUMBER_LINE = re.compile(r"^[\d\s]+$")
# Signs that pdftotext merged the two page columns into one "sentence": a stray footnote letter,
# a quote mark standing alone, or a lower-case word after a full stop.
COLUMN_MIX = re.compile(r"\s[a-z]\s|[.!?]\s+[a-z]|\s[“‘”’]\s|\s[“‘][“‘]")
# Footnote bodies start with the verse number followed by an explanation ("14 Beer-Lahai-Roi maana
# yake ..."); they are hard to tell from verse text, so we drop lines that explain names.
FOOTNOTE_BODY = re.compile(r"^\d+\s+\S+.*\b(maana yake|yaani|au\s+\w+;|Kiebrania|Kiaramu|Kiyunani)\b")
# Inline verse numbers with an optional footnote letter glued on: "4 b“Kwa", "7 fNitalithibitisha".
INLINE_VERSE = re.compile(r"(?<!\S)\d{1,3}\s*[a-z]?\s*(?=[“\"‘A-Z])|(?<!\S)\d{1,3}[a-z]?(?=\s|$)")
INLINE_MARK = re.compile(r"(?<=[,;.:!?”])[a-z](?=\s|$)")     # "Abrahamu,d kwa" -> "Abrahamu, kwa"
SENT_SPLIT = re.compile(r"(?<=[.!?])[”’\"]?\s+(?=[“‘\"]?[A-Z])")
HYPHEN_BREAK = re.compile(r"(\w)-\n(\w)")


def read_pdf(path: Path) -> str:
    if not shutil.which("pdftotext"):
        sys.exit("pdftotext (poppler) is required to read PDFs")
    return subprocess.run(["pdftotext", str(path), "-"], capture_output=True, text=True,
                          check=True).stdout


def clean_bible(raw: str) -> str:
    """Drop the front matter, cross-references, footnotes and numbering; return running text."""
    start = raw.find("DIBAJI")
    lines = raw[start:].splitlines() if start >= 0 else raw.splitlines()
    keep: List[str] = []
    in_xref = False
    for line in lines:
        s = line.strip().replace("‪", "")
        if not s:
            in_xref = False
            keep.append("")
            continue
        if XREF_START.match(s):
            in_xref = True
            continue
        if in_xref and XREF_CONT.match(s):
            continue
        in_xref = False
        if FOOTNOTE_LETTER.match(s) or NUMBER_LINE.match(s) or FOOTNOTE_BODY.match(s):
            continue
        if s.isupper() and len(s.split()) <= 8:          # book and section titles
            keep.append("")
            continue
        keep.append(s)
    text = "\n".join(keep)
    text = HYPHEN_BREAK.sub(r"\1\2", text)
    text = INLINE_VERSE.sub("", text)
    text = INLINE_MARK.sub("", text)
    return text


def sentences(text: str, min_words: int = 4, max_words: int = 60) -> List[str]:
    """Split running text into sentences (paragraph breaks always end a sentence)."""
    out: List[str] = []
    for para in re.split(r"\n\s*\n", text):
        para = " ".join(para.split())
        for s in SENT_SPLIT.split(para):
            s = s.strip(" “”\"‘’")
            n = len(s.split())
            if min_words <= n <= max_words and not re.search(r"\d|www\.|http|\*\*", s) \
                    and not COLUMN_MIX.search(s):
                out.append(s)
    return out


def dedupe(items: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for s in items:
        k = s.lower()
        if k not in seen:
            seen.add(k)
            out.append(s)
    return out


def split(items: List[str], test_every: int = 10, block: int = 200) -> Tuple[List[str], List[str]]:
    """Deterministic train/test split by contiguous blocks, so neighbouring (often near-duplicate)
    verses do not end up on both sides."""
    train, test = [], []
    for i, s in enumerate(items):
        (test if (i // block) % test_every == test_every - 1 else train).append(s)
    return train, test


def bible_sentences(pdf: Path = BIBLE_PDF) -> List[str]:
    cache = DATA_DIR / "bible_sentences.txt"
    if cache.exists():
        return cache.read_text(encoding="utf-8").splitlines()
    return dedupe(sentences(clean_bible(read_pdf(pdf))))


def azimio_sentences(path: Path = AZIMIO) -> List[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return dedupe(sentences(text, min_words=5))


def fingerprint(items: List[str]) -> str:
    return hashlib.sha1("\n".join(items).encode("utf-8")).hexdigest()[:12]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", type=Path, default=BIBLE_PDF)
    ap.add_argument("-o", "--out", type=Path, default=DATA_DIR / "bible_sentences.txt")
    args = ap.parse_args(argv)
    sents = dedupe(sentences(clean_bible(read_pdf(args.pdf))))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(sents) + "\n", encoding="utf-8")
    train, test = split(sents)
    words = sum(len(s.split()) for s in sents)
    print(f"{len(sents)} sentences, {words} words -> {args.out} (train {len(train)}, test {len(test)}, "
          f"sha1 {fingerprint(sents)})")


if __name__ == "__main__":
    main()
