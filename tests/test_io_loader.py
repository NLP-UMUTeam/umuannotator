import json

from umuannotator.io.loader import (
    infer_input_format,
    load_corpus_input,
)


def test_infer_input_format_csv():
    assert infer_input_format("data.csv") == "csv"


def test_infer_input_format_jsonl():
    assert infer_input_format("data.jsonl") == "jsonl"
    assert infer_input_format("data.ndjson") == "jsonl"


def test_infer_input_format_text():
    assert infer_input_format("data.txt") == "text"
    assert infer_input_format("data.text") == "text"


def test_infer_input_format_defaults_to_csv_for_unknown_extension():
    assert infer_input_format("data.unknown") == "csv"


def test_explicit_input_format_overrides_inference():
    assert infer_input_format("data.csv", "jsonl") == "jsonl"


def test_load_csv_input(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text(
        "headline\n"
        "Pizza with mushrooms\n",
        encoding="utf-8",
    )

    corpus = load_corpus_input(
        str(path),
        input_format="csv",
        text_column="headline",
    )

    assert len(corpus.documents) == 1
    assert corpus.documents[0].text == "Pizza with mushrooms"
    assert corpus.documents[0].metadata["doc_id"] == 0


def test_load_jsonl_input(tmp_path):
    path = tmp_path / "data.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "doc-1",
                "text": "Pizza with mushrooms",
                "section": "food",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    corpus = load_corpus_input(
        str(path),
        input_format="jsonl",
        text_column="text",
        id_column="id",
    )

    assert len(corpus.documents) == 1

    document = corpus.documents[0]

    assert document.text == "Pizza with mushrooms"
    assert document.metadata["doc_id"] == "doc-1"
    assert document.metadata["source"]["section"] == "food"


def test_load_text_input(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text(
        "Pizza with mushrooms\n",
        encoding="utf-8",
    )

    corpus = load_corpus_input(
        str(path),
        input_format="text",
    )

    assert len(corpus.documents) == 1
    assert corpus.documents[0].text == "Pizza with mushrooms"