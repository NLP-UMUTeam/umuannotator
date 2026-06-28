import json

from umuannotator.document import Document
from umuannotator.preprocessors.stanza import (
    StanzaPreprocessor,
    text_hash,
)


def test_stanza_preprocessor_loads_cached_metadata(tmp_path):
    cache_dir = tmp_path / "stanza"
    language = "en"
    processors = "tokenize,pos,lemma,ner"
    text = "Pizza with mushrooms"

    key = text_hash(
        text,
        language=language,
        processors=processors,
    )

    cache_path = (
        cache_dir
        / language
        / processors.replace(",", "_")
        / key[:2]
        / f"{key}.json"
    )

    cache_path.parent.mkdir(parents=True)

    payload = {
        "text_hash": key,
        "language": language,
        "processors": processors,
        "tokens": [
            {
                "text": "Pizza",
                "start": 0,
                "end": 5,
                "lemma": "pizza",
                "upos": "NOUN",
            }
        ],
        "entities": [],
    }

    cache_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    document = Document(text=text)

    preprocessor = StanzaPreprocessor(
        language=language,
        processors=processors,
        cache_dir=str(cache_dir),
        use_cache=True,
    )

    result = preprocessor.process_document(document)

    assert "stanza" in result.metadata
    assert result.metadata["stanza"]["text_hash"] == key
    assert result.metadata["stanza"]["tokens"][0]["text"] == "Pizza"


def test_stanza_preprocessor_cache_miss_runs_and_saves(tmp_path, monkeypatch):
    cache_dir = tmp_path / "stanza"
    language = "en"
    processors = "tokenize,pos,lemma,ner"
    text = "Pizza with mushrooms"

    preprocessor = StanzaPreprocessor(
        language=language,
        processors=processors,
        cache_dir=str(cache_dir),
        use_cache=True,
    )

    def fake_run_stanza(value):
        assert value == text

        return {
            "tokens": [
                {
                    "text": "Pizza",
                    "start": 0,
                    "end": 5,
                    "lemma": "pizza",
                    "upos": "NOUN",
                }
            ],
            "entities": [],
        }

    monkeypatch.setattr(
        preprocessor,
        "_run_stanza",
        fake_run_stanza,
    )

    document = Document(text=text)

    result = preprocessor.process_document(document)

    key = text_hash(
        text,
        language=language,
        processors=processors,
    )

    cache_path = preprocessor._cache_path(key)

    assert "stanza" in result.metadata
    assert result.metadata["stanza"]["text_hash"] == key
    assert cache_path.exists()

    cached = json.loads(cache_path.read_text(encoding="utf-8"))

    assert cached["text_hash"] == key
    assert cached["tokens"][0]["text"] == "Pizza"


def test_stanza_preprocessor_no_cache_does_not_write_file(tmp_path, monkeypatch):
    cache_dir = tmp_path / "stanza"
    language = "en"
    processors = "tokenize,pos,lemma,ner"
    text = "Pizza with mushrooms"

    preprocessor = StanzaPreprocessor(
        language=language,
        processors=processors,
        cache_dir=str(cache_dir),
        use_cache=False,
    )

    monkeypatch.setattr(
        preprocessor,
        "_run_stanza",
        lambda value: {
            "tokens": [],
            "entities": [],
        },
    )

    document = Document(text=text)

    result = preprocessor.process_document(document)

    key = text_hash(
        text,
        language=language,
        processors=processors,
    )

    assert "stanza" in result.metadata
    assert result.metadata["stanza"]["text_hash"] == key
    assert not preprocessor._cache_path(key).exists()


def test_stanza_preprocessor_uses_custom_metadata_key(tmp_path, monkeypatch):
    preprocessor = StanzaPreprocessor(
        language="en",
        processors="tokenize,pos,lemma,ner",
        cache_dir=str(tmp_path / "stanza"),
        use_cache=False,
        metadata_key="nlp",
    )

    monkeypatch.setattr(
        preprocessor,
        "_run_stanza",
        lambda value: {
            "tokens": [],
            "entities": [],
        },
    )

    document = Document(text="Pizza")

    result = preprocessor.process_document(document)

    assert "nlp" in result.metadata
    assert "stanza" not in result.metadata