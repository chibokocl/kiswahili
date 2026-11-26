"""
Generate Kiswahili search questions for every paragraph of a set of documents with the Claude API.

    export ANTHROPIC_API_KEY=...            # or any credential the Anthropic SDK resolves
    python -m kiswahili_embed.generate_questions DOCS_DIR --target 6000 --pilot 20   # try first
    python -m kiswahili_embed.generate_questions DOCS_DIR --target 6000

Each paragraph (>= 6 words) is sent with its document name and neighbouring paragraphs; Claude
writes questions a Tanzanian caregiver or health worker might type into a search box, each with
a verbatim ``answer_quote`` from the paragraph.  A question is kept only if its quote really
occurs in the paragraph.  The number of questions per paragraph grows with its length and is
scaled so the total is about ``--target``.

Output (JSON lines, resumable: paragraphs already done are skipped):
``{"id", "doc", "split", "para_id", "question", "who", "answer_quote"}`` where ``split`` is
``train`` or ``test`` per :func:`kiswahili_embed.documents.split_documents`.  Test questions
feed ``evaluate.py --questions``; train questions feed ``train.py --questions``.

The output quotes the source documents, so it is written under ``data/generated/`` (gitignored).
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Sequence
import argparse
import hashlib
import json
import re
import sys
import threading

from .documents import load_documents, split_documents

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_OUT = DATA_DIR / "generated" / "health_questions.jsonl"
MODEL = "claude-opus-5-5"
MIN_WORDS = 6

SYSTEM = """You write evaluation and training data for a Kiswahili semantic search engine over \
Tanzanian health and nutrition documents (Ministry of Health guides, child growth cards, IMCI \
treatment charts, infant feeding leaflets).

Given one PARAGRAPH (plus neighbouring text for context only), write search queries in natural \
Kiswahili that this PARAGRAPH answers.

Rules:
- Every query must be answered by the PARAGRAPH itself, not only by the context.
- Write how real people search: mothers, fathers and caregivers ("caregiver"), and nurses, \
clinical officers and community health workers ("clinician"). Mix full questions, short keyword \
queries, and descriptions of a problem ("Mtoto wangu anakohoa usiku").
- Paraphrase. Do not copy long phrases from the paragraph; use everyday words and synonyms \
where natural. Vary the openings - do not start most queries the same way.
- Use correct standard Kiswahili (Tanzanian usage), including correct noun-class agreement.
- Each query must be distinct in meaning or angle from the others.
- answer_quote: copy EXACTLY, character for character, a span of 4-30 words from the PARAGRAPH \
that answers the query.
- If the paragraph is only a heading, a form field or a fragment with no information, return \
fewer queries or none."""

SCHEMA = {
    "type": "object",
    "properties": {
        "queries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "who": {"type": "string", "enum": ["caregiver", "clinician"]},
                    "answer_quote": {"type": "string"},
                },
                "required": ["question", "who", "answer_quote"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["queries"],
    "additionalProperties": False,
}


def para_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def squash(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def plan(docs, target: int) -> List[Dict]:
    """One job per unique paragraph, with a question count scaled to its length."""
    train_docs, test_docs = split_documents(docs)
    seen, jobs = set(), []
    for d in docs:
        split = "test" if d in test_docs else "train"
        for i, p in enumerate(d.paragraphs):
            if p in seen or len(p.split()) < MIN_WORDS:
                continue
            seen.add(p)
            ctx_before = " ".join(d.paragraphs[max(0, i - 2):i])[-600:]
            ctx_after = " ".join(d.paragraphs[i + 1:i + 3])[:600]
            jobs.append({"doc": d.name, "split": split, "para": p, "para_id": para_id(p),
                         "before": ctx_before, "after": ctx_after, "words": len(p.split())})
    total_words = sum(j["words"] for j in jobs) or 1

    def counts(scale: float) -> List[int]:
        return [max(1, min(12, round(scale * target * j["words"] / total_words))) for j in jobs]

    lo, hi = 0.1, 10.0                      # find the scale whose rounded counts sum to ~target
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if sum(counts(mid)) < target else (lo, mid)
    for j, n in zip(jobs, counts(hi)):
        j["n"] = n
    return jobs


def ask(client, job: Dict) -> List[Dict]:
    prompt = (f"Document: {job['doc']}\n\nContext before (do not write queries about it):\n"
              f"{job['before'] or '-'}\n\nPARAGRAPH:\n{job['para']}\n\nContext after (do not write "
              f"queries about it):\n{job['after'] or '-'}\n\nWrite up to {job['n']} queries.")
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        return []
    text = next((b.text for b in response.content if b.type == "text"), "")
    usage = response.usage
    job["usage"] = (usage.input_tokens, usage.output_tokens)
    return json.loads(text).get("queries", []) if text else []


def fatal(e: Exception) -> bool:
    """Errors that will fail every request (no credit, bad key): stop instead of retrying them all."""
    import anthropic
    if isinstance(e, (anthropic.AuthenticationError, anthropic.PermissionDeniedError)):
        return True
    return isinstance(e, anthropic.BadRequestError) and "credit balance" in str(e).lower()


def validate(job: Dict, queries: Sequence[Dict]) -> List[Dict]:
    para = squash(job["para"])
    out, seen = [], set()
    for q in queries:
        question, quote = squash(q.get("question", "")), squash(q.get("answer_quote", ""))
        if len(question.split()) < 2 or not quote or quote not in para:
            continue
        key = question.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"doc": job["doc"], "split": job["split"], "para_id": job["para_id"],
                    "question": question, "who": q.get("who", "caregiver"), "answer_quote": quote})
    return out


def run(docs_paths: Sequence[Path], out: Path, target: int, workers: int, pilot: int) -> None:
    import anthropic
    client = anthropic.Anthropic(max_retries=6)
    jobs = plan(load_documents(docs_paths), target)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        done = {json.loads(l)["para_id"] for l in out.read_text(encoding="utf-8").splitlines() if l}
        done |= {l.strip() for l in (out.with_suffix(".done")).read_text().splitlines()} \
            if out.with_suffix(".done").exists() else set()
    todo = [j for j in jobs if j["para_id"] not in done]
    if pilot:
        todo = todo[:pilot]
    print(f"{len(jobs)} paragraphs, {sum(j['n'] for j in jobs)} questions planned; "
          f"{len(jobs) - len([j for j in jobs if j['para_id'] not in done])} already done, "
          f"{len(todo)} to do now", file=sys.stderr)
    lock = threading.Lock()
    kept = asked = tin = tout = 0
    with ThreadPoolExecutor(workers) as pool, out.open("a", encoding="utf-8") as f, \
            out.with_suffix(".done").open("a") as done_f:
        futures = {pool.submit(ask, client, j): j for j in todo}
        for k, fut in enumerate(as_completed(futures), 1):
            job = futures[fut]
            try:
                queries = fut.result()
            except Exception as e:                       # keep going; rerun resumes
                if fatal(e):
                    print(f"stopping: {type(e).__name__}: {e}\nNothing is lost: rerun the same "
                          f"command to resume.", file=sys.stderr)
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                print(f"error on {job['para_id']}: {type(e).__name__}: {e}", file=sys.stderr)
                continue
            rows = validate(job, queries)
            with lock:
                asked += len(queries)
                kept += len(rows)
                i, o = job.get("usage", (0, 0))
                tin, tout = tin + i, tout + o
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
                done_f.write(job["para_id"] + "\n")
                f.flush(), done_f.flush()
            if k % 25 == 0 or k == len(todo):
                cost = tin / 1e6 * 4 + tout / 1e6 * 20
                print(f"{k}/{len(todo)} paragraphs, {kept}/{asked} questions kept, "
                      f"{tin} in / {tout} out tokens, ~${cost:.2f}", file=sys.stderr)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docs", nargs="+", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--target", type=int, default=6000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--pilot", type=int, default=0, help="only this many paragraphs (cost check)")
    args = ap.parse_args(argv)
    run(args.docs, args.out, args.target, args.workers, args.pilot)


if __name__ == "__main__":
    main()
