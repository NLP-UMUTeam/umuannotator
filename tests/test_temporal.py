from umuannotator.annotators.temporal import TemporalAnnotator
from umuannotator.document.model import Document


def test_temporal_annotator_detects_ayer():
    document = Document(
        text="Pedro viajó ayer a Valencia."
    )

    annotator = TemporalAnnotator(language="es")
    result = annotator.annotate(document)

    texts = [annotation.text.lower() for annotation in result.annotations]

    assert "ayer" in texts


def test_temporal_annotator_keeps_offsets():
    text = "Pedro viajó ayer a Valencia."
    document = Document(text=text)

    annotator = TemporalAnnotator(language="es")
    result = annotator.annotate(document)

    annotation = result.annotations[0]

    assert text[annotation.start:annotation.end] == annotation.text 