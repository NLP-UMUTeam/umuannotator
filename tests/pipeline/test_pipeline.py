from umuannotator.annotators.registry import build_annotators
from umuannotator.pipeline import AnnotationPipeline


def test_pipeline_with_ontology_annotator():
    annotators = build_annotators(
        ["ontology"],
        ontology_path="resources/pizza.owl",
        language="es",
    )

    pipeline = AnnotationPipeline(annotators)

    document = pipeline.run_text(
        "Me gusta la pizza hawaiana con queso."
    )

    labels = [annotation.label for annotation in document.annotations]
    texts = [annotation.text.lower() for annotation in document.annotations]

    assert "HawaiianPizza" in labels
    assert "Cheese" in labels
    assert "pizza hawaiana" in texts
    assert "queso" in texts


def test_pipeline_keeps_offsets():
    annotators = build_annotators(
        ["ontology"],
        ontology_path="resources/pizza.owl",
        language="es",
    )

    pipeline = AnnotationPipeline(annotators)

    text = "Me gusta la pizza hawaiana."
    document = pipeline.run_text(text)

    annotation = next(
        annotation
        for annotation in document.annotations
        if annotation.label == "HawaiianPizza"
    )

    assert text[annotation.start:annotation.end] == annotation.text