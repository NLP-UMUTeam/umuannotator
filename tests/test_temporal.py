from umuannotator.annotators.temporal import TemporalAnnotator
from umuannotator.document.model import Document


def annotate(text: str):
    document = Document(text=text)
    annotator = TemporalAnnotator(language="es")
    return annotator.annotate(document)


def texts(result):
    return [annotation.text.lower() for annotation in result.annotations]


def test_temporal_annotator_detects_ayer():
    result = annotate("Pedro viajó ayer a Valencia.")

    assert "ayer" in texts(result)


def test_temporal_annotator_detects_manana():
    result = annotate("Mañana iremos a una pizzería italiana.")

    assert "mañana" in texts(result)


def test_temporal_annotator_does_not_detect_a_una():
    result = annotate("Mañana iremos a una pizzería italiana.")

    assert "a una" not in texts(result)


def test_temporal_annotator_detects_proximo_lunes():
    result = annotate("El próximo lunes comeremos pizza.")

    assert any(
        "próximo lunes" in text
        for text in texts(result)
    )


def test_temporal_annotator_detects_en_dos_semanas():
    result = annotate("Volveremos en dos semanas.")

    assert "en dos semanas" in texts(result)


def test_temporal_annotator_keeps_offsets():
    text = "Pedro viajó ayer a Valencia."
    result = annotate(text)

    for annotation in result.annotations:
        assert text[annotation.start:annotation.end] == annotation.text


def test_temporal_annotator_labels_are_temporal():
    result = annotate("Ayer comí pizza y mañana volveré.")

    assert result.annotations

    for annotation in result.annotations:
        assert annotation.layer == "temporal"
        assert annotation.type == "temporal"
        assert annotation.source == "duckling-temporal"


def test_temporal_annotator_has_value_metadata():
    result = annotate("Ayer comí pizza.")

    annotation = result.annotations[0]

    assert "value" in annotation.metadata
    assert "locale" in annotation.metadata
    assert "timezone" in annotation.metadata