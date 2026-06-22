from umuannotator.annotators.registry import build_annotators
from umuannotator.pipeline import AnnotationPipeline
from umuannotator.metrics import TfidfScorer


def test_pipeline_run_texts_with_tfidf():
    annotators = build_annotators(
        ["ontology"],
        ontology_path="resources/pizza.owl",
        language="es",
    )

    pipeline = AnnotationPipeline(annotators)

    documents = pipeline.run_texts([
        "Me gusta la pizza hawaiana.",
        "Me gusta la pizza margarita.",
    ])

    scorer = TfidfScorer(layer="ontology")
    scored_documents = scorer.score(documents)

    assert len(scored_documents) == 2

    annotations = scored_documents[0].annotations

    assert any(
        annotation.label == "HawaiianPizza"
        and "tfidf" in annotation.metadata
        for annotation in annotations
    )