import json

from umuannotator.io.output import (
    infer_output_format,
    write_output,
)


def test_infer_output_format_json():
    assert infer_output_format("results.json") == "json"


def test_infer_output_format_jsonl():
    assert infer_output_format("results.jsonl") == "jsonl"
    assert infer_output_format("results.ndjson") == "jsonl"


def test_infer_output_format_text():
    assert infer_output_format("results.txt") == "text"
    assert infer_output_format("results.text") == "text"


def test_infer_output_format_defaults_to_json_for_unknown_extension():
    assert infer_output_format("results.unknown") == "json"


def test_infer_output_format_stdout_defaults_to_jsonl():
    assert infer_output_format("-") == "jsonl"


def test_explicit_output_format_overrides_inference():
    assert infer_output_format("results.json", "jsonl") == "jsonl"


def test_infer_output_format_explicit_overrides_stdout_default():
    assert infer_output_format("-", "json") == "json"


def test_write_json_output_compact_by_default(tmp_path):
    path = tmp_path / "results.json"

    data = {
        "documents": [
            {
                "text": "Pizza",
                "metadata": {
                    "doc_id": "doc-1",
                    "stanza": {
                        "tokens": [
                            {
                                "text": "Pizza",
                                "upos": "NOUN",
                            }
                        ]
                    },
                },
                "annotations": [],
            }
        ],
        "metadata": {
            "documents": 1,
            "layer_colors": {
                "ontology": "#ffd6d6",
            },
        },
    }

    write_output(
        data,
        str(path),
        output_format="json",
    )

    loaded = json.loads(path.read_text(encoding="utf-8"))

    assert loaded == {
        "documents": [
            {
                "text": "Pizza",
                "annotations": [],
                "metadata": {
                    "doc_id": "doc-1",
                },
            }
        ],
        "metadata": {
            "layer_colors": {
                "ontology": "#ffd6d6",
            },
        },
    }


def test_write_json_output_full_profile(tmp_path):
    path = tmp_path / "results.json"

    data = {
        "documents": [
            {
                "text": "Pizza",
                "annotations": [],
            }
        ],
        "metadata": {
            "documents": 1,
        },
    }

    write_output(
        data,
        str(path),
        output_format="json",
        output_profile="full",
    )

    loaded = json.loads(path.read_text(encoding="utf-8"))

    assert loaded["documents"][0]["text"] == "Pizza"
    assert loaded["metadata"]["documents"] == 1


def test_write_jsonl_output_one_line_per_document_compact_by_default(tmp_path):
    path = tmp_path / "results.jsonl"

    data = {
        "documents": [
            {
                "text": "Pizza",
                "metadata": {
                    "doc_id": "doc-1",
                    "stanza": {
                        "tokens": [],
                    },
                },
                "annotations": [],
            },
            {
                "text": "Pasta",
                "metadata": {
                    "doc_id": "doc-2",
                    "stanza": {
                        "tokens": [],
                    },
                },
                "annotations": [],
            },
        ],
        "metadata": {
            "documents": 2,
        },
    }

    write_output(
        data,
        str(path),
        output_format="jsonl",
    )

    lines = path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])

    assert first == {
        "text": "Pizza",
        "annotations": [],
        "metadata": {
            "doc_id": "doc-1",
        },
    }

    assert second == {
        "text": "Pasta",
        "annotations": [],
        "metadata": {
            "doc_id": "doc-2",
        },
    }


def test_write_jsonl_output_full_profile_one_line_per_document(tmp_path):
    path = tmp_path / "results.jsonl"

    data = {
        "documents": [
            {
                "text": "Pizza",
                "metadata": {
                    "doc_id": "doc-1",
                    "stanza": {
                        "tokens": [
                            {
                                "text": "Pizza",
                            }
                        ]
                    },
                },
                "annotations": [],
            },
            {
                "text": "Pasta",
                "metadata": {
                    "doc_id": "doc-2",
                },
                "annotations": [],
            },
        ],
        "metadata": {
            "documents": 2,
        },
    }

    write_output(
        data,
        str(path),
        output_format="jsonl",
        output_profile="full",
    )

    lines = path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])

    assert first["text"] == "Pizza"
    assert first["metadata"]["doc_id"] == "doc-1"
    assert first["metadata"]["stanza"] == {
        "tokens": [
            {
                "text": "Pizza",
            }
        ]
    }

    assert second["text"] == "Pasta"
    assert second["metadata"]["doc_id"] == "doc-2"


def test_write_text_output(tmp_path):
    path = tmp_path / "results.txt"

    data = {
        "documents": [
            {"text": "Pizza"},
            {"text": "Pasta"},
        ]
    }

    write_output(
        data,
        str(path),
        output_format="text",
    )

    assert path.read_text(encoding="utf-8") == "Pizza\nPasta\n"