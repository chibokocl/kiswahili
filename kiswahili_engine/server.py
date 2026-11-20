"""
Tiny local server for trying the checker in a browser (standard library only).

    python -m kiswahili_engine.server            # then open http://127.0.0.1:8000
    python -m kiswahili_engine.server --port 9000

Endpoints: ``GET /`` (the page), ``POST /api/check`` {"text", "min_confidence"},
``GET /api/lookup?w=word``.  Binds to 127.0.0.1 only.
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .checker import Checker, apply_suggestions

PAGE = Path(__file__).resolve().parent / "web" / "index.html"
MAX_BODY = 200_000


def lookup(chk: Checker, word: str) -> dict:
    w = word.strip().lower()
    ns = chk.ns
    verb = ns.verb_parser.parse(w)[:3] if w else []
    return {
        "word": w,
        "known_word": bool(w) and chk._is_known(w, w),
        "corpus_frequency": chk.freq.get(w, 0),
        "noun": [{"lemma": e.lemma, "ngeli": e.ngeli, "number": e.number, "source": e.source,
                  "animate": e.animate} for e in (ns.noun_lexicon.lookup(w) if ns.noun_lexicon else [])],
        "inanimate": bool(ns.noun_lexicon and ns.noun_lexicon.is_inanimate(w)),
        "verb": [{**p.to_dict(), "morphemes": p.morphemes()} for p in verb if p.score >= 0.5],
        "concord": [{"stem": f.stem, "kind": f.kind, "class": f.cls} for f in chk.concord.lookup(w)],
        "invariable_adjective": chk.concord.is_invariable(w),
    }


def make_handler(chk: Checker):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code=200):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")

        def do_GET(self):
            url = urlparse(self.path)
            if url.path in ("/", "/index.html"):
                self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            elif url.path == "/api/lookup":
                word = parse_qs(url.query).get("w", [""])[0][:60]
                self._json(lookup(chk, word))
            else:
                self._json({"error": "not found"}, 404)

        def do_POST(self):
            if urlparse(self.path).path != "/api/check":
                return self._json({"error": "not found"}, 404)
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self._json({"error": "text too long"}, 413)
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
                text = str(data.get("text", ""))
                min_conf = float(data.get("min_confidence", 0.6))
            except (ValueError, TypeError):
                return self._json({"error": "bad request"}, 400)
            issues = chk.check(text, min_conf)
            self._json({"issues": [i.to_dict() for i in issues],
                        "corrected": apply_suggestions(text, issues)})

        def log_message(self, fmt, *args):        # quiet
            pass

    return Handler


def main(argv=None):
    ap = argparse.ArgumentParser(description="Local Kiswahili checker page")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args(argv)
    print("Loading lexicons...", flush=True)
    chk = Checker()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(chk))
    print(f"Ready: http://127.0.0.1:{args.port}   (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
