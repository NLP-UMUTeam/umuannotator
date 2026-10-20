import math

from umuannotator.document.model import Annotation, Document
from umuannotator.metrics.tfidf import TfidfScorer


def test_tfidf_adds_score_to_annotations():
    documents = [
        Document(
            text="pizza hawaiana",
            annotations=[
                Annotation(
                    start=0,
                    end=15,
                    text="pizza hawaiana",
                    label="HawaiianPizza",
                    layer="ontology",
                )
            ],
        ),
        Document(
            text="pizza margarita",
            annotations=[
                Annotation(
                    start=0,
                    end=15,
                    text="pizza margarita",
                    label="Margherita",
                    layer="ontology",
                )
            ],
        ),
    ]

    scorer = TfidfScorer(layer="ontology")
    result = scorer.score(documents)

    annotation = result[0].annotations[0]

    assert annotation.score == 1.0
    assert annotation.metadata["tf"] == 1
    assert annotation.metadata["df"] == 1
    assert annotation.metadata["idf"] == 1.0
    assert annotation.metadata["tfidf"] == 1.0


def test_tfidf_uses_document_frequency():
    documents = [
        Document(
            text="pizza hawaiana",
            annotations=[
                Annotation(0, 5, "pizza", "Pizza", "ontology"),
                Annotation(6, 15, "hawaiana", "HawaiianPizza", "ontology"), 
            ],
        ),
        Document(
            text="pizza margarita",
            annotations=[
                Annotation(0, 5, "pizza", "Pizza", "ontology"),
                Annotation(6, 15, "margarita", "Margherita", "ontology"),
            ],
        ),
    ]

    scorer = TfidfScorer(layer="ontology")
    result = scorer.score(documents)

    pizza_annotation = result[0].annotations[0]
    hawaiian_annotation = result[0].annotations[1]

    assert pizza_annotation.metadata["df"] == 2
    assert pizza_annotation.metadata["idf"] == 0.0
    assert pizza_annotation.metadata["tfidf"] == 0.0

    assert hawaiian_annotation.metadata["df"] == 1
    assert hawaiian_annotation.metadata["idf"] == 1.0
    assert hawaiian_annotation.metadata["tfidf"] == 1.0

from copy import deepcopy

from umuannotator.document import (
    Annotation,
    Document,
)
from umuannotator.metrics import (
    TfidfScorer,
)


def test_tfidf_fit_and_score_document_matches_score():
    documents = [
        Document(
            text="uno",
            annotations=[
                Annotation(
                    start=0,
                    end=3,
                    text="uno",
                    label="A",
                    layer="ontology",
                )
            ],
        ),
        Document(
            text="dos",
            annotations=[
                Annotation(
                    start=0,
                    end=3,
                    text="dos",
                    label="A",
                    layer="ontology",
                ),
                Annotation(
                    start=0,
                    end=3,
                    text="dos",
                    label="B",
                    layer="ontology",
                ),
            ],
        ),
    ]

    one_step = deepcopy(
        documents
    )
    two_step = deepcopy(
        documents
    )

    TfidfScorer().score(
        one_step
    )

    scorer = TfidfScorer()
    scorer.fit(
        two_step
    )

    for document in two_step:
        scorer.score_document(
            document
        )

    assert two_step == one_step

def test_tfidf_can_use_external_statistics():
    document = Document(
        text="uno",
        annotations=[
            Annotation(
                start=0,
                end=3,
                text="uno",
                label="A",
                layer="ontology",
            )
        ],
    )

    scorer = TfidfScorer()

    scorer.fit_statistics(
        total_documents=10,
        document_frequency={
            "A": 5,
        },
    )

    scorer.score_document(
        document
    )

    annotation = (
        document.annotations[0]
    )

    assert annotation.metadata[
        "tf"
    ] == 1

    assert annotation.metadata[
        "df"
    ] == 5

    assert annotation.metadata[
        "idf"
    ] == math.log(10 / 5)

    assert annotation.metadata[
        "tfidf"
    ] == math.log(10 / 5)

    assert annotation.score == (
        math.log(10 / 5)
    )

import pytest


def test_tfidf_score_document_requires_fit():
    scorer = TfidfScorer()

    document = Document(
        text="test"
    )

    with pytest.raises(
        RuntimeError,
        match="must be fitted",
    ):
        scorer.score_document(
            document
        )