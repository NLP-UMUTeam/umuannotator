from umuannotator.document import Corpus
from umuannotator.metrics import TfidfScorer
from umuannotator.metrics.extended_tfidf import ExtendedTfidfScorer

from umuannotator.annotators.registry import build_annotators
from umuannotator.pipeline import AnnotationPipeline

from umuannotator.ontology.loader import load_ontology
from umuannotator.ontology.index import build_index
from umuannotator.ontology.graph import build_graph


def test_extended_tfidf_generates_parent_scores():

    annotators = build_annotators(
        ["ontology"],
        ontology_path="resources/pizza.owl",
        language="es",
    )

    pipeline = AnnotationPipeline(annotators)

    corpus = Corpus(
        documents=pipeline.run_texts([
            "Me gusta la pizza hawaiana"
        ])
    )

    corpus = TfidfScorer().score(corpus)

    graph = load_ontology("resources/pizza.owl")
    concepts = build_index(graph)

    ontology_graph = build_graph(concepts)

    corpus = ExtendedTfidfScorer(
        ontology_graph,
        decay=0.5,
        max_distance=5,
    ).score(corpus)

    scores = corpus.documents[0].metadata["tfidf_extended"]

    assert "HawaiianPizza" in scores
    assert "Pizza" in scores