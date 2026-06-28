from umuannotator.annotators.quantity import QuantityAnnotator
from umuannotator.document import Annotation, Document

def make_annotation(text: str, start: int = 0):
    return Annotation(
        start=start,
        end=start + len(text),
        text=text,
        label="NUMBER",
        layer="cantidades",
        type="quantity",
    )


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

def test_quantity_label_for_number():
    annotator = QuantityAnnotator()

    assert annotator._quantity_label({"dim": "number"}) == "NUMBER"
    assert annotator._quantity_label({"dim": "amount-of-money"}) == "MONEY"
    assert annotator._quantity_label({"dim": "distance"}) == "DISTANCE"