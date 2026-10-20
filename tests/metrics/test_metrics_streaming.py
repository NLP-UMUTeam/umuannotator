import json

import json
from copy import deepcopy


from umuannotator.document import (
    Annotation,
    Document,
)

from umuannotator.metrics.streaming import (
    apply_streaming_tfidf,
    collect_tfidf_statistics,
)
from umuannotator.metrics.tfidf import TfidfScorer
from umuannotator.serialization.documents import (
    deserialize_document,
    serialize_document,
)


def test_collect_tfidf_statistics(
    tmp_path,
):
    input_path = tmp_path / "input.jsonl"

    documents = [
        {
            "text": "doc 1",
            "annotations": [
                {
                    "label": "A",
                    "layer": "ontology",
                },
                {
                    "label": "A",
                    "layer": "ontology",
                },
                {
                    "label": "X",
                    "layer": "other",
                },
            ],
        },
        {
            "text": "doc 2",
            "annotations": [
                {
                    "label": "A",
                    "layer": "ontology",
                },
                {
                    "label": "B",
                    "layer": "ontology",
                },
            ],
        },
        {
            "text": "doc 3",
            "annotations": [
                {
                    "label": "B",
                    "layer": "ontology",
                },
            ],
        },
    ]

    with input_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        for document in documents:
            f.write(
                json.dumps(document)
                + "\n"
            )

    total_documents, df = (
        collect_tfidf_statistics(
            str(input_path),
            layer="ontology",
        )
    )

    assert total_documents == 3
    assert df["A"] == 2
    assert df["B"] == 2
    assert "X" not in df

def test_collect_tfidf_statistics_empty(
    tmp_path,
):
    input_path = tmp_path / "input.jsonl"
    input_path.write_text(
        "",
        encoding="utf-8",
    )

    total_documents, df = (
        collect_tfidf_statistics(
            str(input_path)
        )
    )

    assert total_documents == 0
    assert df == {}


def test_apply_streaming_tfidf_matches_in_memory(
    tmp_path,
):
    input_path = tmp_path / "input.jsonl"
    output_path = tmp_path / "output.jsonl"

    documents = [
        Document(
            text="doc 1",
            annotations=[
                Annotation(
                    start=0,
                    end=1,
                    text="A",
                    label="A",
                    layer="ontology",
                    metadata={
                        "concept_id": "A",
                    },
                ),
                Annotation(
                    start=2,
                    end=3,
                    text="A",
                    label="A",
                    layer="ontology",
                    metadata={
                        "concept_id": "A",
                    },
                ),
            ],
        ),
        Document(
            text="doc 2",
            annotations=[
                Annotation(
                    start=0,
                    end=1,
                    text="A",
                    label="A",
                    layer="ontology",
                    metadata={
                        "concept_id": "A",
                    },
                ),
                Annotation(
                    start=2,
                    end=3,
                    text="B",
                    label="B",
                    layer="ontology",
                    metadata={
                        "concept_id": "B",
                    },
                ),
            ],
        ),
    ]

    with input_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        for document in documents:
            serialized = serialize_document(
                document,
                output_profile="full",
            )

            f.write(
                json.dumps(
                    serialized,
                    ensure_ascii=False,
                )
                + "\n"
            )

    expected = deepcopy(
        documents
    )

    TfidfScorer(
        layer="ontology",
    ).score(
        expected
    )

    apply_streaming_tfidf(
        str(input_path),
        str(output_path),
        tfidf_scorer=TfidfScorer(
            layer="ontology",
        ),
        output_profile="full",
    )

    actual = []

    with output_path.open(
        "r",
        encoding="utf-8",
    ) as f:
        for line in f:
            actual.append(
                deserialize_document(
                    json.loads(line)
                )
            )

    assert actual == expected