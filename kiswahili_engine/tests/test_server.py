"""Smoke tests for the local web tester (real HTTP on an ephemeral port)."""

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from kiswahili_engine.checker import Checker
from kiswahili_engine.server import make_handler


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Checker()))
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def post(self, payload, raw=None):
        data = raw if raw is not None else json.dumps(payload).encode()
        req = urllib.request.Request(self.base + "/api/check", data=data,
                                     headers={"Content-Type": "application/json"})
        return json.load(urllib.request.urlopen(req))

    def test_page_is_served(self):
        html = urllib.request.urlopen(self.base + "/").read().decode()
        self.assertIn("<textarea", html)
        self.assertIn("/api/check", html)

    def test_check(self):
        out = self.post({"text": "Kitabu umeanguka."})
        (issue,) = [i for i in out["issues"] if i["rule"] == "AGR-SV"]
        self.assertEqual(issue["suggestions"][0]["text"], "kimeanguka")
        self.assertEqual(out["corrected"], "Kitabu kimeanguka.")

    def test_clean_text_has_no_issues(self):
        self.assertEqual(self.post({"text": "Mtoto anakula chakula."})["issues"], [])

    def test_lookup(self):
        d = json.load(urllib.request.urlopen(self.base + "/api/lookup?w=anakula"))
        self.assertEqual(d["verb"][0]["segmentation"], "a-na-ku-l-a")
        d = json.load(urllib.request.urlopen(self.base + "/api/lookup?w=mtoto"))
        self.assertEqual(d["noun"][0]["ngeli"], "1/2")

    def test_bad_requests(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.post(None, raw=b"not json")
        self.assertEqual(cm.exception.code, 400)
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(self.base + "/nope")
        self.assertEqual(cm.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
