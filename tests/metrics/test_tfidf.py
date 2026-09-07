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