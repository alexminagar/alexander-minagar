import json
from http.server import BaseHTTPRequestHandler
from threading import Lock

MODEL_NAME = "fr_core_news_md"
MODEL_VERSION = "3.8.0"
MAX_CHARACTERS = 500
MAX_BODY_BYTES = 8192
_nlp = None
_load_lock = Lock()
_parse_lock = Lock()

POS_LABELS = {
    "ADJ": "Adjective / adjectif",
    "ADP": "Adposition / préposition",
    "ADV": "Adverb / adverbe",
    "AUX": "Auxiliary verb / auxiliaire",
    "CCONJ": "Coordinating conjunction",
    "DET": "Determiner / déterminant",
    "INTJ": "Interjection",
    "NOUN": "Common noun / nom commun",
    "NUM": "Numeral / numéral",
    "PART": "Particle / particule",
    "PRON": "Pronoun / pronom",
    "PROPN": "Proper noun / nom propre",
    "PUNCT": "Punctuation / ponctuation",
    "SCONJ": "Subordinating conjunction",
    "SYM": "Symbol / symbole",
    "VERB": "Verb / verbe",
    "X": "Other or unclassified",
}

DEPENDENCY_LABELS = {
    "ROOT": "Sentence root",
    "acl": "Clause modifying a noun",
    "acl:relcl": "Relative clause",
    "advcl": "Adverbial clause",
    "advmod": "Adverbial modifier",
    "amod": "Adjectival modifier",
    "appos": "Apposition",
    "aux": "Auxiliary",
    "aux:pass": "Passive auxiliary",
    "case": "Case marker / preposition",
    "cc": "Coordinating conjunction",
    "ccomp": "Clausal complement",
    "compound": "Compound element",
    "conj": "Coordinated element",
    "cop": "Copula / linking verb",
    "csubj": "Clausal subject",
    "csubj:pass": "Passive clausal subject",
    "dep": "Unspecified dependency",
    "det": "Determiner",
    "discourse": "Discourse element",
    "expl": "Expletive / grammatical placeholder",
    "expl:comp": "Reflexive complement marker",
    "expl:pass": "Reflexive passive marker",
    "expl:pv": "Pronominal verb marker",
    "expl:subj": "Expletive subject",
    "fixed": "Fixed expression element",
    "flat": "Flat expression element",
    "flat:name": "Name element",
    "iobj": "Indirect object",
    "mark": "Clause marker",
    "nmod": "Noun modifier",
    "nsubj": "Subject / sujet",
    "nsubj:pass": "Passive subject",
    "nummod": "Numeric modifier",
    "obj": "Direct object / complément d'objet direct",
    "obl": "Oblique modifier or complement",
    "obl:arg": "Oblique argument",
    "obl:mod": "Oblique modifier",
    "orphan": "Orphaned element",
    "parataxis": "Loosely connected clause",
    "punct": "Punctuation",
    "vocative": "Direct address",
    "xcomp": "Open clausal complement",
}

MORPHOLOGY_LABELS = {
    "Gender": {"Fem": "Feminine", "Masc": "Masculine", "Neut": "Neuter"},
    "Number": {"Sing": "Singular", "Plur": "Plural"},
    "Person": {"1": "First person", "2": "Second person", "3": "Third person"},
    "Tense": {"Pres": "Present", "Past": "Past", "Imp": "Imperfect", "Fut": "Future", "Pqp": "Pluperfect"},
    "Mood": {"Ind": "Indicative", "Sub": "Subjunctive", "Cnd": "Conditional", "Imp": "Imperative"},
    "VerbForm": {"Fin": "Finite verb", "Inf": "Infinitive", "Part": "Participle", "Ger": "Gerund"},
    "Voice": {"Act": "Active", "Pass": "Passive", "Mid": "Middle"},
    "Definite": {"Def": "Definite", "Ind": "Indefinite", "Spec": "Specific"},
    "PronType": {"Art": "Article", "Dem": "Demonstrative", "Ind": "Indefinite", "Int": "Interrogative", "Neg": "Negative", "Prs": "Personal", "Rel": "Relative", "Tot": "Total quantifier"},
    "Poss": {"Yes": "Possessive"},
    "Reflex": {"Yes": "Reflexive"},
    "Polarity": {"Neg": "Negative", "Pos": "Positive"},
    "NumType": {"Card": "Cardinal number", "Ord": "Ordinal number", "Mult": "Multiplicative number"},
}


class RequestError(Exception):
    def __init__(self, status, code, message):
        self.status = status
        self.code = code
        self.message = message
        super().__init__(message)


class ModelUnavailable(Exception):
    pass


def validate_payload(payload):
    if not isinstance(payload, dict):
        raise RequestError(400, "invalid_payload", "Send a JSON object with a text field.")
    text = payload.get("text")
    if not isinstance(text, str):
        raise RequestError(400, "invalid_text", "The text field must be a string.")
    if not text.strip():
        raise RequestError(400, "empty_text", "Enter a French sentence to analyze.")
    if len(text) > MAX_CHARACTERS:
        raise RequestError(413, "text_too_long", f"Use no more than {MAX_CHARACTERS} characters.")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in text):
        raise RequestError(400, "invalid_unicode", "Use valid Unicode text.")
    if any(ord(character) < 32 and character not in "\t\n\r" for character in text):
        raise RequestError(400, "invalid_characters", "Remove control characters from the text.")
    return text


def get_nlp():
    global _nlp
    if _nlp is None:
        with _load_lock:
            if _nlp is None:
                try:
                    import spacy
                    pipeline = spacy.load(MODEL_NAME, exclude=["ner"])
                    pipeline.max_length = MAX_CHARACTERS + 1
                    _nlp = pipeline
                except Exception as error:
                    raise ModelUnavailable("The French language model is unavailable.") from error
    return _nlp


def morphology_description(features):
    labels = []
    for feature, values in features.items():
        for value in values:
            labels.append(MORPHOLOGY_LABELS.get(feature, {}).get(value, f"{feature}: {value}"))
    return " · ".join(labels) if labels else "Not specified by the model"


def analyze_text(text):
    text = validate_payload({"text": text})
    pipeline = get_nlp()
    analysis_text = text.translate(str.maketrans({"’": "'", "‘": "'", "ʼ": "'"}))
    with _parse_lock:
        document = pipeline(analysis_text)
    tokens = []
    for token in document:
        if token.is_space:
            continue
        features = {key: value.split(",") for key, value in token.morph.to_dict().items()}
        dependency = DEPENDENCY_LABELS.get(token.dep_)
        if dependency is None:
            base_label = DEPENDENCY_LABELS.get(token.dep_.split(":")[0])
            dependency = f"{base_label} ({token.dep_})" if base_label else token.dep_ or "Not specified"
        end = token.idx + len(token.text)
        tokens.append({
            "id": token.i,
            "text": text[token.idx:end],
            "start": token.idx,
            "end": end,
            "start_utf16": len(text[:token.idx].encode("utf-16-le")) // 2,
            "end_utf16": len(text[:end].encode("utf-16-le")) // 2,
            "lemma": token.lemma_,
            "pos": token.pos_,
            "pos_label": POS_LABELS.get(token.pos_, token.pos_ or "Not specified"),
            "dependency": token.dep_,
            "dependency_label": dependency,
            "head": text[token.head.idx:token.head.idx + len(token.head.text)],
            "head_id": None if token.head.is_space else token.head.i,
            "morphology": features,
            "morphology_label": morphology_description(features),
        })
    warnings = [
        "These are statistical model predictions and can be wrong, including on ordinary sentences. Use a trusted grammar reference to check unfamiliar results.",
        "Features not reported by the model are left unspecified. This is an analysis tool, not a grammar-correction or translation service.",
    ]
    if analysis_text != text:
        warnings.append("Typographic apostrophes were normalized internally for analysis. The displayed sentence and token text preserve your original characters.")
    return {
        "text": text,
        "model": f"{MODEL_NAME} {pipeline.meta.get('version', MODEL_VERSION)}",
        "tokens": tokens,
        "summary": {
            "token_count": len(tokens),
            "word_count": sum(any(character.isalnum() for character in token["text"]) for token in tokens),
            "sentence_count": sum(1 for sentence in document.sents if sentence.text.strip()),
        },
        "warnings": warnings,
    }


class handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload, head_only=False):
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def health_payload(self):
        return {
            "status": "ok",
            "model": f"{MODEL_NAME} {MODEL_VERSION}",
            "max_characters": MAX_CHARACTERS,
            "model_loaded": _nlp is not None,
        }

    def do_GET(self):
        self.send_json(200, self.health_payload())

    def do_HEAD(self):
        self.send_json(200, self.health_payload(), head_only=True)

    def do_POST(self):
        try:
            if self.headers.get_content_type() != "application/json":
                raise RequestError(415, "unsupported_content_type", "Send the request as application/json.")
            if self.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise RequestError(415, "unsupported_encoding", "Send uncompressed UTF-8 JSON.")
            if self.headers.get("Transfer-Encoding"):
                raise RequestError(400, "unsupported_transfer_encoding", "Send the request with a Content-Length header.")
            raw_length = self.headers.get("Content-Length")
            if raw_length is None:
                raise RequestError(411, "length_required", "A Content-Length header is required.")
            try:
                length = int(raw_length)
            except ValueError as error:
                raise RequestError(400, "invalid_length", "Content-Length must be a positive integer.") from error
            if length <= 0:
                raise RequestError(400, "empty_body", "Send a JSON request body.")
            if length > MAX_BODY_BYTES:
                raise RequestError(413, "body_too_large", "The request body is too large.")
            raw_body = self.rfile.read(length)
            if len(raw_body) != length:
                raise RequestError(400, "incomplete_body", "The request body was incomplete.")
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise RequestError(400, "invalid_json", "Send valid UTF-8 JSON.") from error
            text = validate_payload(payload)
            result = analyze_text(text)
            self.send_json(200, result)
        except RequestError as error:
            self.send_json(error.status, {"error": {"code": error.code, "message": error.message}})
        except ModelUnavailable:
            self.send_json(503, {"error": {"code": "model_unavailable", "message": "The French analysis service is temporarily unavailable. Please try again later."}})
        except Exception:
            self.send_json(500, {"error": {"code": "analysis_failed", "message": "This text could not be analyzed. Please try a shorter French sentence."}})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Allow", "GET, HEAD, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def method_not_allowed(self):
        self.send_json(405, {"error": {"code": "method_not_allowed", "message": "Use POST to analyze text or GET to check the endpoint."}})

    do_PUT = method_not_allowed
    do_PATCH = method_not_allowed
    do_DELETE = method_not_allowed

    def log_message(self, format, *args):
        return
