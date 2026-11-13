import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from api import analyze
import serve


class AnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), analyze.handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, payload=None, raw=None, content_type="application/json", method="POST", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=30)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if raw is None else raw
        request_headers = {"Content-Type": content_type}
        request_headers.update(headers or {})
        connection.request(method, "/api/analyze", body=body, headers=request_headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), json.loads(response.read())
        connection.close()
        return result

    def test_real_french_model_reports_structure(self):
        status, headers, result = self.request({"text": "Les enfants regardent le film."})
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(result["model"], "fr_core_news_md 3.8.0")
        by_text = {token["text"]: token for token in result["tokens"]}
        self.assertEqual(by_text["regardent"]["lemma"], "regarder")
        self.assertEqual(by_text["regardent"]["pos"], "VERB")
        self.assertEqual(by_text["enfants"]["dependency"], "nsubj")
        self.assertEqual(by_text["enfants"]["morphology"]["Number"], ["Plur"])
        self.assertEqual(by_text["film"]["dependency"], "obj")
        self.assertEqual(result["summary"], {"token_count": 6, "word_count": 5, "sentence_count": 1})

    def test_elisions_accents_punctuation_and_offsets_are_preserved(self):
        text = "🙂 L’élève n’aime pas l’été.\nElle préfère l’hiver !"
        status, headers, result = self.request({"text": text})
        self.assertEqual(status, 200)
        self.assertEqual(result["text"], text)
        self.assertTrue(any(token["pos"] == "PUNCT" for token in result["tokens"]))
        self.assertTrue(any("élève" in token["text"] for token in result["tokens"]))
        encoded = text.encode("utf-16-le")
        identifiers = {token["id"] for token in result["tokens"]}
        for token in result["tokens"]:
            self.assertEqual(text[token["start"]:token["end"]], token["text"])
            self.assertEqual(encoded[token["start_utf16"] * 2:token["end_utf16"] * 2].decode("utf-16-le"), token["text"])
            self.assertTrue(token["head_id"] is None or token["head_id"] in identifiers)

    def test_typographic_apostrophes_are_normalized_without_changing_display(self):
        status, headers, result = self.request({"text": "L’élève n’aime pas l’été."})
        self.assertEqual(status, 200)
        by_text = {token["text"]: token for token in result["tokens"]}
        self.assertEqual(by_text["L’"]["pos"], "DET")
        self.assertEqual(by_text["L’"]["lemma"], "le")
        self.assertEqual(by_text["été"]["pos"], "NOUN")
        self.assertEqual(by_text["été"]["lemma"], "été")
        self.assertTrue(any("apostrophes" in warning for warning in result["warnings"]))

    def test_past_tense_example_keeps_verb_and_noun_distinct(self):
        status, headers, result = self.request({"text": "Nous avons visité le musée hier."})
        self.assertEqual(status, 200)
        by_text = {token["text"]: token for token in result["tokens"]}
        self.assertEqual(by_text["visité"]["pos"], "VERB")
        self.assertEqual(by_text["visité"]["lemma"], "visiter")
        self.assertEqual(by_text["musée"]["pos"], "NOUN")
        self.assertEqual(by_text["musée"]["lemma"], "musée")

    def test_invalid_requests_are_rejected_without_model_work(self):
        cases = [None, [], "bonjour", {}, {"text": None}, {"text": 5}, {"text": False}, {"text": " \n\t"}, {"text": "bonjour\x00"}]
        with patch.object(analyze, "get_nlp", side_effect=AssertionError("Model must not load")):
            for payload in cases:
                with self.subTest(payload=payload):
                    status, headers, result = self.request(payload)
                    self.assertEqual(status, 400)
                    self.assertIn("message", result["error"])
            status, headers, result = self.request({"text": "é" * 501})
            self.assertEqual(status, 413)
            self.assertEqual(result["error"]["code"], "text_too_long")
            status, headers, result = self.request(raw=b"x" * 8193)
            self.assertEqual(status, 413)
            status, headers, result = self.request(raw=b"{bad json}")
            self.assertEqual(status, 400)
            status, headers, result = self.request(raw=b"\xff")
            self.assertEqual(status, 400)
            status, headers, result = self.request(raw=b'{"text":"\\ud800"}')
            self.assertEqual(status, 400)
            status, headers, result = self.request({"text": "Bonjour."}, content_type="text/plain")
            self.assertEqual(status, 415)

    def test_boundary_counts_characters_not_utf8_bytes(self):
        text = "é" * 500
        self.assertEqual(analyze.validate_payload({"text": text}), text)
        status, headers, result = self.request({"text": text})
        self.assertEqual(status, 200)
        self.assertEqual(result["text"], text)

    def test_model_failure_is_an_honest_service_error(self):
        with patch.object(analyze, "get_nlp", side_effect=analyze.ModelUnavailable()):
            status, headers, result = self.request({"text": "Bonjour."})
        self.assertEqual(status, 503)
        self.assertEqual(result["error"]["code"], "model_unavailable")
        self.assertNotIn("tokens", result)

    def test_health_endpoint_is_lightweight(self):
        with patch.object(analyze, "get_nlp", side_effect=AssertionError("Health must not load the model")):
            status, headers, result = self.request(method="GET")
        self.assertEqual(status, 200)
        self.assertEqual(result["max_characters"], 500)
        self.assertIsInstance(result["model_loaded"], bool)

    def test_unknown_morphology_is_not_invented(self):
        self.assertEqual(analyze.morphology_description({}), "Not specified by the model")
        self.assertEqual(analyze.morphology_description({"Unfamiliar": ["X"]}), "Unfamiliar: X")


class LocalServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls.directory.name)
        (cls.root / "index.html").write_text("<!doctype html><title>Portfolio</title>")
        (cls.root / "secret.py").write_text("not a static asset")
        (cls.root / ".private").write_text("not a static asset")
        cls.root_patch = patch.object(serve, "ROOT", cls.root)
        cls.root_patch.start()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), serve.LocalHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.root_patch.stop()
        cls.directory.cleanup()

    def get(self, path):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request("GET", path)
        response = connection.getresponse()
        status, body = response.status, response.read()
        connection.close()
        return status, body

    def test_static_page_and_api_share_one_origin(self):
        status, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn(b"Portfolio", body)
        status, body = self.get("/api/analyze")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["status"], "ok")

    def test_source_private_paths_and_traversal_are_not_served(self):
        for path in ["/secret.py", "/.private", "/%2eprivate", "/%2e%2e/secret.py", "/api/analyze.py", "/tests/", "/requirements.txt"]:
            with self.subTest(path=path):
                status, body = self.get(path)
                self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
