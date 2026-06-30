from umuannotator.annotators.quantity import QuantityAnnotator
from umuannotator.document import Annotation, Document
from umuannotator.lang.quantity import get_quantity_rules


def annotate(text: str):
    document = Document(text=text)
    annotator = QuantityAnnotator(language="es")
    return annotator.annotate(document)


def annotation_texts(result):
    return [annotation.text for annotation in result.annotations]


def assert_annotation(result, *, text: str, label: str | None = None):
    matches = [
        annotation
        for annotation in result.annotations
        if annotation.text == text
        and (label is None or annotation.label == label)
    ]

    assert matches, (
        f"Expected annotation text={text!r}, label={label!r}. "
        f"Got: {[(a.text, a.label) for a in result.annotations]}"
    )

    return matches[0]


def assert_no_annotation(result, *, text: str):
    texts = annotation_texts(result)

    assert text not in texts, (
        f"Did not expect annotation text={text!r}. "
        f"Got: {[(a.text, a.label) for a in result.annotations]}"
    )


def make_annotation(
    text: str,
    *,
    start: int = 0,
    label: str = "NUMBER",
):
    return Annotation(
        start=start,
        end=start + len(text),
        text=text,
        label=label,
        layer="cantidades",
        source="duckling-quantity",
        type="quantity",
        metadata={},
    )


def test_quantity_detects_number_plus_multiplier_as_single_quantity():
    result = annotate("El portal asigna por error 22.000 millones.")

    annotation = assert_annotation(result, text="22.000 millones")

    assert annotation.type == "quantity"
    assert annotation.layer == "cantidades"


def test_quantity_does_not_split_number_plus_multiplier():
    result = annotate("El portal asigna por error 22.000 millones.")

    assert_no_annotation(result, text="22.000")
    assert_no_annotation(result, text="millones")


def test_quantity_removes_un_when_stanza_token_is_det():
    document = Document(text="un pueblo")

    document.metadata["stanza"] = {
        "tokens": [
            {
                "text": "un",
                "start": 0,
                "end": 2,
                "upos": "DET",
            }
        ]
    }

    annotation = make_annotation("un")
    annotator = QuantityAnnotator()

    assert annotator._is_false_positive_determiner(
        annotation,
        document,
    )


def test_quantity_keeps_un_when_stanza_token_is_num():
    document = Document(text="un millón")

    document.metadata["stanza"] = {
        "tokens": [
            {
                "text": "un",
                "start": 0,
                "end": 2,
                "upos": "NUM",
            }
        ]
    }

    annotation = make_annotation("un")
    annotator = QuantityAnnotator()

    assert not annotator._is_false_positive_determiner(
        annotation,
        document,
    )


def test_quantity_keeps_digit_number():
    document = Document(text="22.000 millones")

    document.metadata["stanza"] = {
        "tokens": [
            {
                "text": "22.000",
                "start": 0,
                "end": 6,
                "upos": "NUM",
            }
        ]
    }

    annotation = make_annotation("22.000")
    annotator = QuantityAnnotator()

    assert not annotator._is_false_positive_determiner(
        annotation,
        document,
    )


def test_quantity_keeps_un_when_no_stanza_metadata():
    document = Document(text="un pueblo")
    annotation = make_annotation("un")
    annotator = QuantityAnnotator()

    assert not annotator._is_false_positive_determiner(
        annotation,
        document,
    )


def test_quantity_keeps_un_when_offsets_do_not_match():
    document = Document(text="un pueblo")

    document.metadata["stanza"] = {
        "tokens": [
            {
                "text": "un",
                "start": 3,
                "end": 5,
                "upos": "DET",
            }
        ]
    }

    annotation = make_annotation("un")
    annotator = QuantityAnnotator()

    assert not annotator._is_false_positive_determiner(
        annotation,
        document,
    )


def test_quantity_label_for_supported_dimensions():
    annotator = QuantityAnnotator()

    assert annotator._quantity_label({"dim": "number"}) == "NUMBER"
    assert annotator._quantity_label({"dim": "amount-of-money"}) == "MONEY"
    assert annotator._quantity_label({"dim": "distance"}) == "DISTANCE"
    assert annotator._quantity_label({"dim": "volume"}) == "VOLUME"
    assert annotator._quantity_label({"dim": "temperature"}) == "TEMPERATURE"
    assert annotator._quantity_label({"dim": "ordinal"}) == "ORDINAL"
    assert annotator._quantity_label({"dim": "quantity"}) == "QUANTITY"
    assert annotator._quantity_label({"dim": "unknown"}) == "QUANTITY"


def test_quantity_loads_spanish_rules():
    rules = get_quantity_rules("es")

    assert "un" in rules.determiner_number_words
    assert rules.multipliers["millones"] == 1_000_000
    assert rules.multiplier_after_number_re is not None


def test_quantity_unknown_language_uses_empty_rules():
    rules = get_quantity_rules("xx")

    assert rules.determiner_number_words == set()
    assert rules.multipliers == {}
    assert rules.multiplier_after_number_re is None