from umuannotator.annotation_enrichers.age import AgeEnricher
from umuannotator.document.model import Annotation, Document


def test_refines_human_nominal_duration_as_age():
    text = "Una mujer de 77 años fue atendida."

    document = Document(
        text=text,
        annotations=[
            Annotation(
                start=4,
                end=9,
                text="mujer",
                label="LEXICAL_SEMANTICS",
                layer="lexical_semantics",
                source="wordnet",
                metadata={
                    "semantic_classes": ["HUMAN"],
                },
            ),
            Annotation(
                start=13,
                end=20,
                text="77 años",
                label="DURATION",
                layer="temporal",
                source="duckling-temporal",
                metadata={
                    "duckling_dim": "duration",
                    "normalized": 77,
                },
            ),
        ],
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "Una",
                                "start": 0,
                                "end": 3,
                                "lemma": "uno",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                            },
                            {
                                "id": 2,
                                "text": "mujer",
                                "start": 4,
                                "end": 9,
                                "lemma": "mujer",
                                "upos": "NOUN",
                                "head": 7,
                                "deprel": "nsubj",
                            },
                            {
                                "id": 3,
                                "text": "de",
                                "start": 10,
                                "end": 12,
                                "lemma": "de",
                                "upos": "ADP",
                                "head": 5,
                                "deprel": "case",
                            },
                            {
                                "id": 4,
                                "text": "77",
                                "start": 13,
                                "end": 15,
                                "lemma": "77",
                                "upos": "NUM",
                                "head": 5,
                                "deprel": "nummod",
                            },
                            {
                                "id": 5,
                                "text": "años",
                                "start": 16,
                                "end": 20,
                                "lemma": "año",
                                "upos": "NOUN",
                                "head": 2,
                                "deprel": "nmod",
                            },
                        ],
                    }
                ],
            }
        },
    )

    enricher = AgeEnricher()

    result = enricher.enrich(document)

    temporal = next(
        annotation
        for annotation in result.annotations
        if annotation.layer == "temporal"
    )

    assert temporal.label == "AGE"
    assert temporal.source == "duckling-temporal"

    assert temporal.metadata["duckling_dim"] == "duration"
    assert temporal.metadata["normalized"] == 77
    assert temporal.metadata["resolved_from"] == "DURATION"
    assert temporal.metadata["refined_by"] == "age"
    assert temporal.metadata["rule"] == "human_nominal_age"

    assert temporal.metadata["age_evidence"]["human_head"] == {
        "text": "mujer",
        "lemma": "mujer",
        "start": 4,
        "end": 9,
    }


def test_preserves_non_human_nominal_duration():
    text = "Una investigación de 2 años terminó ayer."

    document = Document(
        text=text,
        annotations=[
            Annotation(
                start=4,
                end=17,
                text="investigación",
                label="LEXICAL_SEMANTICS",
                layer="lexical_semantics",
                source="wordnet",
                metadata={
                    "semantic_classes": ["PROCESS"],
                },
            ),
            Annotation(
                start=21,
                end=27,
                text="2 años",
                label="DURATION",
                layer="temporal",
                source="duckling-temporal",
                metadata={
                    "duckling_dim": "duration",
                    "normalized": 2,
                },
            ),
        ],
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "Una",
                                "start": 0,
                                "end": 3,
                                "lemma": "uno",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                            },
                            {
                                "id": 2,
                                "text": "investigación",
                                "start": 4,
                                "end": 17,
                                "lemma": "investigación",
                                "upos": "NOUN",
                                "head": 6,
                                "deprel": "nsubj",
                            },
                            {
                                "id": 3,
                                "text": "de",
                                "start": 18,
                                "end": 20,
                                "lemma": "de",
                                "upos": "ADP",
                                "head": 5,
                                "deprel": "case",
                            },
                            {
                                "id": 4,
                                "text": "2",
                                "start": 21,
                                "end": 22,
                                "lemma": "2",
                                "upos": "NUM",
                                "head": 5,
                                "deprel": "nummod",
                            },
                            {
                                "id": 5,
                                "text": "años",
                                "start": 23,
                                "end": 27,
                                "lemma": "año",
                                "upos": "NOUN",
                                "head": 2,
                                "deprel": "nmod",
                            },
                        ],
                    }
                ],
            }
        },
    )

    enricher = AgeEnricher()

    result = enricher.enrich(document)

    temporal = next(
        annotation
        for annotation in result.annotations
        if annotation.layer == "temporal"
    )

    assert temporal.label == "DURATION"
    assert temporal.metadata["duckling_dim"] == "duration"
    assert temporal.metadata["normalized"] == 2

    assert "resolved_from" not in temporal.metadata
    assert "refined_by" not in temporal.metadata
    assert "rule" not in temporal.metadata
    assert "age_evidence" not in temporal.metadata