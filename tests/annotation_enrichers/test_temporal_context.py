from umuannotator.annotation_enrichers.temporal_context import (
    TemporalContextEnricher,
)
from umuannotator.document.model import Annotation, Document


def test_temporal_context_enricher_is_initially_noop() -> None:
    annotation = Annotation(
        start=10,
        end=24,
        text="28 de abril",
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        metadata={
            "normalized": "2026-04-28T00:00:00+02:00",
            "reference_datetime": "2025-05-03T12:00:00+02:00",
            "reference_datetime_source": "source.publication_date",
        },
    )

    document = Document(
        text="El apagón del 28 de abril",
        annotations=[annotation],
        metadata={
            "source": {
                "publication_date": "2025-05-03T12:00:00+02:00",
            }
        },
    )

    enricher = TemporalContextEnricher()
    result = enricher.enrich(document)

    assert result is document
    assert annotation.label == "DATE"
    assert (
        annotation.metadata["normalized"]
        == "2026-04-28T00:00:00+02:00"
    )

from umuannotator.annotation_enrichers.temporal_context import (
    TemporalContextEnricher,
)
from umuannotator.document.model import Annotation, Document


def make_temporal_annotation(
    *,
    text: str,
    normalized: str,
    grain: str = "day",
) -> Annotation:
    return Annotation(
        start=0,
        end=len(text),
        text=text,
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        metadata={
            "normalized": normalized,
            "grain": grain,
            "raw_value": {
                "value": normalized,
            },
        },
    )


def make_document(
    annotation: Annotation,
    *,
    publication_date: str,
) -> Document:
    return Document(
        text=annotation.text,
        annotations=[annotation],
        metadata={
            "source": {
                "publication_date": publication_date,
            }
        },
    )


def test_corrects_recent_day_month_resolved_to_next_year() -> None:
    annotation = make_temporal_annotation(
        text="del 28 de abril",
        normalized="2026-04-28T00:00:00+02:00",
    )

    annotation.start = 10
    annotation.end = 25

    document = Document(
        text="El apagón del 28 de abril provocó problemas.",
        annotations=[annotation],
        metadata={
            "source": {
                "publication_date": "2025-05-03T12:00:00+02:00",
            },
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "apagón",
                                "start": 3,
                                "end": 9,
                                "lemma": "apagón",
                                "upos": "NOUN",
                                "feats": None,
                                "head": 3,
                                "deprel": "nsubj",
                            },
                            {
                                "id": 2,
                                "text": "28",
                                "start": 14,
                                "end": 16,
                                "lemma": "28",
                                "upos": "NUM",
                                "feats": None,
                                "head": 1,
                                "deprel": "nmod",
                            },
                            {
                                "id": 3,
                                "text": "provocó",
                                "start": 26,
                                "end": 33,
                                "lemma": "provocar",
                                "upos": "VERB",
                                "feats": (
                                    "Mood=Ind|Tense=Past|VerbForm=Fin"
                                ),
                                "head": 0,
                                "deprel": "root",
                            },
                        ],
                    }
                ]
            },
        },
    )

    TemporalContextEnricher().enrich(document)

    assert annotation.metadata["normalized"].startswith(
        "2025-04-28T00:00:00"
    )

    resolution = annotation.metadata["context_resolution"]

    assert resolution["rule"] == "day_month_recent_past"
    assert resolution["previous_normalized"].startswith(
        "2026-04-28T00:00:00"
    )
    assert resolution["distance_days"] == 5
    assert resolution["temporal_orientation"] == "PAST"

    predicate = resolution["predicate_context"]["predicate"]

    assert predicate["lemma"] == "provocar"
    assert predicate["tense"] == "Past"


def test_does_not_correct_without_past_evidence() -> None:
    annotation = make_temporal_annotation(
        text="el 28 de abril",
        normalized="2026-04-28T00:00:00+02:00",
    )

    document = Document(
        text="el 28 de abril",
        annotations=[annotation],
        metadata={
            "source": {
                "publication_date": "2025-05-03T12:00:00+02:00",
            },
        },
    )

    TemporalContextEnricher().enrich(document)

    assert annotation.metadata["normalized"].startswith(
        "2026-04-28T00:00:00"
    )
    assert "context_resolution" not in annotation.metadata

def test_does_not_change_explicit_year() -> None:
    annotation = make_temporal_annotation(
        text="28 de abril de 2026",
        normalized="2026-04-28T00:00:00+02:00",
    )
    document = make_document(
        annotation,
        publication_date="2025-05-03T12:00:00+02:00",
    )

    TemporalContextEnricher().enrich(document)

    assert annotation.metadata["normalized"].startswith(
        "2026-04-28T00:00:00"
    )
    assert "context_resolution" not in annotation.metadata


def test_does_not_change_future_day_month_in_same_year() -> None:
    annotation = make_temporal_annotation(
        text="2 de junio",
        normalized="2025-06-02T00:00:00+02:00",
    )
    document = make_document(
        annotation,
        publication_date="2025-05-03T12:00:00+02:00",
    )

    TemporalContextEnricher().enrich(document)

    assert annotation.metadata["normalized"].startswith(
        "2025-06-02T00:00:00"
    )
    assert "context_resolution" not in annotation.metadata


def test_does_not_change_distant_past_candidate() -> None:
    annotation = make_temporal_annotation(
        text="28 de abril",
        normalized="2026-04-28T00:00:00+02:00",
    )
    document = make_document(
        annotation,
        publication_date="2025-12-30T12:00:00+01:00",
    )

    TemporalContextEnricher().enrich(document)

    assert annotation.metadata["normalized"].startswith(
        "2026-04-28T00:00:00"
    )
    assert "context_resolution" not in annotation.metadata

def test_future_tense_blocks_past_correction() -> None:
    annotation = make_temporal_annotation(
        text="el 28 de abril",
        normalized="2026-04-28T00:00:00+02:00",
    )

    document = Document(
        text="El acto se celebrará el 28 de abril.",
        annotations=[annotation],
        metadata={
            "source": {
                "publication_date": "2025-05-03T12:00:00+02:00",
            },
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "celebrará",
                                "start": 11,
                                "end": 20,
                                "lemma": "celebrar",
                                "upos": "VERB",
                                "feats": (
                                    "Mood=Ind|Tense=Fut|VerbForm=Fin"
                                ),
                                "head": 0,
                                "deprel": "root",
                            },
                            {
                                "id": 2,
                                "text": "28",
                                "start": 24,
                                "end": 26,
                                "lemma": "28",
                                "upos": "NUM",
                                "feats": None,
                                "head": 1,
                                "deprel": "obl",
                            },
                        ],
                    }
                ]
            },
        },
    )

    # Adjust the synthetic annotation to the real span.
    annotation.start = 21
    annotation.end = 35

    TemporalContextEnricher().enrich(document)

    assert annotation.metadata["normalized"].startswith(
        "2026-04-28T00:00:00"
    )
    assert "context_resolution" not in annotation.metadata


def test_past_tense_allows_past_correction() -> None:
    annotation = make_temporal_annotation(
        text="del 28 de abril",
        normalized="2026-04-28T00:00:00+02:00",
    )

    annotation.start = 10
    annotation.end = 25

    document = Document(
        text="El apagón del 28 de abril provocó problemas.",
        annotations=[annotation],
        metadata={
            "source": {
                "publication_date": "2025-05-03T12:00:00+02:00",
            },
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "apagón",
                                "start": 3,
                                "end": 9,
                                "lemma": "apagón",
                                "upos": "NOUN",
                                "feats": None,
                                "head": 3,
                                "deprel": "nsubj",
                            },
                            {
                                "id": 2,
                                "text": "28",
                                "start": 14,
                                "end": 16,
                                "lemma": "28",
                                "upos": "NUM",
                                "feats": None,
                                "head": 1,
                                "deprel": "nmod",
                            },
                            {
                                "id": 3,
                                "text": "provocó",
                                "start": 26,
                                "end": 33,
                                "lemma": "provocar",
                                "upos": "VERB",
                                "feats": (
                                    "Mood=Ind|Tense=Past|VerbForm=Fin"
                                ),
                                "head": 0,
                                "deprel": "root",
                            },
                        ],
                    }
                ]
            },
        },
    )

    TemporalContextEnricher().enrich(document)

    assert annotation.metadata["normalized"].startswith(
        "2025-04-28T00:00:00"
    )

    resolution = annotation.metadata["context_resolution"]

    assert resolution["temporal_orientation"] == "PAST"

    predicate = resolution["predicate_context"]["predicate"]

    assert predicate["lemma"] == "provocar"
    assert predicate["tense"] == "Past"


def _weekday_document(
    *,
    text: str,
    annotation_start: int,
    annotation_end: int,
    annotation_text: str,
    normalized: str,
    publication_date: str,
    words: list[dict],
) -> Document:
    return Document(
        text=text,
        annotations=[
            Annotation(
                start=annotation_start,
                end=annotation_end,
                text=annotation_text,
                label="DATE",
                layer="temporal",
                source="duckling-temporal",
                type="temporal",
                subtype="time",
                metadata={
                    "grain": "day",
                    "normalized": normalized,
                },
            ),
        ],
        metadata={
            "source": {
                "publication_date": publication_date,
            },
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": words,
                    },
                ],
            },
        },
    )