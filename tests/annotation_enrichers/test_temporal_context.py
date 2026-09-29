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
def _word(
    *,
    id: int,
    text: str,
    start: int,
    end: int,
    lemma: str,
    upos: str,
    head: int,
    deprel: str,
    feats: str | None = None,
) -> dict:
    return {
        "id": id,
        "text": text,
        "start": start,
        "end": end,
        "lemma": lemma,
        "upos": upos,
        "feats": feats,
        "head": head,
        "deprel": deprel,
    }

def _date_time_document(
    *,
    text: str,
    publication_date: str,
    date_start: int,
    date_end: int,
    date_text: str,
    date_normalized: str,
    time_start: int,
    time_end: int,
    words: list[dict],
) -> Document:
    return Document(
        text=text,
        annotations=[
            Annotation(
                start=date_start,
                end=date_end,
                text=date_text,
                label="DATE",
                layer="temporal",
                source="duckling-temporal",
                type="temporal",
                subtype="time",
                metadata={
                    "grain": "day",
                    "normalized": date_normalized,
                },
            ),
            Annotation(
                start=time_start,
                end=time_end,
                text=text[time_start:time_end],
                label="TIME",
                layer="temporal",
                source="duckling-temporal",
                type="temporal",
                subtype="time",
                metadata={
                    "grain": "minute",
                    "normalized": "12:33",
                    "date_resolved": False,
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

def test_resolves_time_from_past_weekday_on_same_predicate() -> None:
    text = "El lunes comenzó la reunión a las 12:33."
    document = _date_time_document(
        text=text,
        publication_date="2025-04-29T12:00:00+02:00",
        date_start=3,
        date_end=8,
        date_text="lunes",
        date_normalized="2025-04-28T00:00:00+02:00",
        time_start=29,
        time_end=41,
        words=[
            _word(
                id=1,
                text="lunes",
                start=3,
                end=8,
                lemma="lunes",
                upos="NOUN",
                head=2,
                deprel="obl",
            ),
            _word(
                id=2,
                text="comenzó",
                start=9,
                end=16,
                lemma="comenzar",
                upos="VERB",
                head=0,
                deprel="root",
                feats="Mood=Ind|Tense=Past|VerbForm=Fin",
            ),
            _word(
                id=3,
                text="12:33",
                start=35,
                end=40,
                lemma="12:33",
                upos="NUM",
                head=2,
                deprel="obl",
            ),
        ],
    )
    TemporalContextEnricher(language="es").enrich(document)
    time_annotation = document.annotations[1]
    assert (
        time_annotation.metadata["normalized"]
        == "2025-04-28T12:33:00+02:00"
    )
    assert time_annotation.metadata["date_resolved"] is True
    resolution = time_annotation.metadata["context_resolution"]
    assert resolution["rule"] == "time_from_date_same_predicate"
    assert resolution["previous_normalized"] == "12:33"

def test_resolves_time_from_future_weekday_on_same_predicate() -> None:
    text = "El lunes comenzará la reunión a las 12:33."
    document = _date_time_document(
        text=text,
        publication_date="2025-05-01T12:00:00+02:00",
        date_start=3,
        date_end=8,
        date_text="lunes",
        date_normalized="2025-05-05T00:00:00+02:00",
        time_start=31,
        time_end=43,
        words=[
            _word(
                id=1,
                text="lunes",
                start=3,
                end=8,
                lemma="lunes",
                upos="NOUN",
                head=2,
                deprel="obl",
            ),
            _word(
                id=2,
                text="comenzará",
                start=9,
                end=18,
                lemma="comenzar",
                upos="VERB",
                head=0,
                deprel="root",
                feats="Mood=Ind|Tense=Fut|VerbForm=Fin",
            ),
            _word(
                id=3,
                text="12:33",
                start=37,
                end=42,
                lemma="12:33",
                upos="NUM",
                head=2,
                deprel="obl",
            ),
        ],
    )
    TemporalContextEnricher(language="es").enrich(document)
    assert (
        document.annotations[1].metadata["normalized"]
        == "2025-05-05T12:33:00+02:00"
    )

def test_resolves_time_from_day_month_on_same_predicate() -> None:
    text = "El 28 de abril comenzó la reunión a las 12:33."
    document = _date_time_document(
        text=text,
        publication_date="2025-05-03T12:00:00+02:00",
        date_start=3,
        date_end=14,
        date_text="28 de abril",
        date_normalized="2025-04-28T00:00:00+02:00",
        time_start=35,
        time_end=47,
        words=[
            _word(
                id=1,
                text="28",
                start=3,
                end=5,
                lemma="28",
                upos="NUM",
                head=2,
                deprel="obl",
            ),
            _word(
                id=2,
                text="comenzó",
                start=15,
                end=22,
                lemma="comenzar",
                upos="VERB",
                head=0,
                deprel="root",
                feats="Mood=Ind|Tense=Past|VerbForm=Fin",
            ),
            _word(
                id=3,
                text="12:33",
                start=41,
                end=46,
                lemma="12:33",
                upos="NUM",
                head=2,
                deprel="obl",
            ),
        ],
    )
    TemporalContextEnricher(language="es").enrich(document)
    assert (
        document.annotations[1].metadata["normalized"]
        == "2025-04-28T12:33:00+02:00"
    )

def test_does_not_resolve_time_from_date_in_previous_sentence() -> None:
    text = "El lunes comenzó la reunión. Terminó a las 12:33."
    date_annotation = Annotation(
        start=3,
        end=8,
        text="lunes",
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        subtype="time",
        metadata={
            "grain": "day",
            "normalized": "2025-04-28T00:00:00+02:00",
        },
    )
    time_annotation = Annotation(
        start=37,
        end=49,
        text="a las 12:33",
        label="TIME",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        subtype="time",
        metadata={
            "grain": "minute",
            "normalized": "12:33",
            "date_resolved": False,
        },
    )
    document = Document(
        text=text,
        annotations=[date_annotation, time_annotation],
        metadata={
            "source": {
                "publication_date": "2025-04-29T12:00:00+02:00",
            },
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            _word(
                                id=1,
                                text="lunes",
                                start=3,
                                end=8,
                                lemma="lunes",
                                upos="NOUN",
                                head=2,
                                deprel="obl",
                            ),
                            _word(
                                id=2,
                                text="comenzó",
                                start=9,
                                end=16,
                                lemma="comenzar",
                                upos="VERB",
                                head=0,
                                deprel="root",
                                feats="Mood=Ind|Tense=Past|VerbForm=Fin",
                            ),
                        ],
                    },
                    {
                        "id": 1,
                        "words": [
                            _word(
                                id=1,
                                text="Terminó",
                                start=29,
                                end=36,
                                lemma="terminar",
                                upos="VERB",
                                head=0,
                                deprel="root",
                                feats="Mood=Ind|Tense=Past|VerbForm=Fin",
                            ),
                            _word(
                                id=2,
                                text="12:33",
                                start=43,
                                end=48,
                                lemma="12:33",
                                upos="NUM",
                                head=1,
                                deprel="obl",
                            ),
                        ],
                    },
                ],
            },
        },
    )
    TemporalContextEnricher(language="es").enrich(document)
    assert time_annotation.metadata["normalized"] == "12:33"
    assert time_annotation.metadata["date_resolved"] is False
    assert "context_resolution" not in time_annotation.metadata

def test_does_not_propagate_date_across_coordinated_predicates() -> None:
    text = "El lunes comenzó la reunión y terminó a las 12:33."
    document = _date_time_document(
        text=text,
        publication_date="2025-04-29T12:00:00+02:00",
        date_start=3,
        date_end=8,
        date_text="lunes",
        date_normalized="2025-04-28T00:00:00+02:00",
        time_start=39,
        time_end=51,
        words=[
            _word(
                id=1,
                text="lunes",
                start=3,
                end=8,
                lemma="lunes",
                upos="NOUN",
                head=2,
                deprel="obl",
            ),
            _word(
                id=2,
                text="comenzó",
                start=9,
                end=16,
                lemma="comenzar",
                upos="VERB",
                head=0,
                deprel="root",
                feats="Mood=Ind|Tense=Past|VerbForm=Fin",
            ),
            _word(
                id=3,
                text="terminó",
                start=30,
                end=37,
                lemma="terminar",
                upos="VERB",
                head=2,
                deprel="conj",
                feats="Mood=Ind|Tense=Past|VerbForm=Fin",
            ),
            _word(
                id=4,
                text="12:33",
                start=45,
                end=50,
                lemma="12:33",
                upos="NUM",
                head=3,
                deprel="obl",
            ),
        ],
    )
    TemporalContextEnricher(language="es").enrich(document)
    time_annotation = document.annotations[1]
    assert time_annotation.metadata["normalized"] == "12:33"
    assert time_annotation.metadata["date_resolved"] is False
    assert "context_resolution" not in time_annotation.metadata

def test_uses_date_attached_to_same_coordinated_predicate() -> None:
    text = (
        "El lunes comenzó la reunión y el martes "
        "terminó a las 12:33."
    )
    monday = Annotation(
        start=3,
        end=8,
        text="lunes",
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        subtype="time",
        metadata={
            "grain": "day",
            "normalized": "2025-04-28T00:00:00+02:00",
        },
    )
    tuesday = Annotation(
        start=35,
        end=41,
        text="martes",
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        subtype="time",
        metadata={
            "grain": "day",
            "normalized": "2025-04-29T00:00:00+02:00",
        },
    )
    time_annotation = Annotation(
        start=50,
        end=62,
        text="a las 12:33",
        label="TIME",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        subtype="time",
        metadata={
            "grain": "minute",
            "normalized": "12:33",
            "date_resolved": False,
        },
    )
    document = Document(
        text=text,
        annotations=[monday, tuesday, time_annotation],
        metadata={
            "source": {
                "publication_date": "2025-04-30T12:00:00+02:00",
            },
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            _word(
                                id=1,
                                text="lunes",
                                start=3,
                                end=8,
                                lemma="lunes",
                                upos="NOUN",
                                head=2,
                                deprel="obl",
                            ),
                            _word(
                                id=2,
                                text="comenzó",
                                start=9,
                                end=16,
                                lemma="comenzar",
                                upos="VERB",
                                head=0,
                                deprel="root",
                                feats="Mood=Ind|Tense=Past|VerbForm=Fin",
                            ),
                            _word(
                                id=3,
                                text="martes",
                                start=35,
                                end=41,
                                lemma="martes",
                                upos="NOUN",
                                head=4,
                                deprel="obl",
                            ),
                            _word(
                                id=4,
                                text="terminó",
                                start=42,
                                end=49,
                                lemma="terminar",
                                upos="VERB",
                                head=2,
                                deprel="conj",
                                feats="Mood=Ind|Tense=Past|VerbForm=Fin",
                            ),
                            _word(
                                id=5,
                                text="12:33",
                                start=56,
                                end=61,
                                lemma="12:33",
                                upos="NUM",
                                head=4,
                                deprel="obl",
                            ),
                        ],
                    },
                ],
            },
        },
    )
    TemporalContextEnricher(language="es").enrich(document)
    assert (
        time_annotation.metadata["normalized"]
        == "2025-04-29T12:33:00+02:00"
    )
    assert time_annotation.metadata["date_resolved"] is True


def _month_only_document(
    *,
    text: str,
    predicate_text: str,
    predicate_lemma: str,
    predicate_start: int,
    predicate_end: int,
    predicate_feats: str,
    month_start: int,
    month_end: int,
) -> tuple[Document, Annotation]:
    month_annotation = Annotation(
        start=month_start,
        end=month_end,
        text="marzo",
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        subtype="time",
        metadata={
            "grain": "month",
            "normalized": "2026-03-01T00:00:00+01:00",
            "raw_value": {
                "grain": "month",
                "type": "value",
                "value": "2026-03-01T00:00:00+01:00",
            },
        },
    )

    document = Document(
        text=text,
        annotations=[month_annotation],
        metadata={
            "source": {
                "publication_date": "2025-05-03T12:00:00+02:00",
            },
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            _word(
                                id=1,
                                text=predicate_text,
                                start=predicate_start,
                                end=predicate_end,
                                lemma=predicate_lemma,
                                upos="VERB",
                                head=0,
                                deprel="root",
                                feats=predicate_feats,
                            ),
                            _word(
                                id=2,
                                text="marzo",
                                start=month_start,
                                end=month_end,
                                lemma="marzo",
                                upos="NOUN",
                                head=1,
                                deprel="obl",
                            ),
                        ],
                    },
                ],
            },
        },
    )

    return document, month_annotation


def test_resolves_past_month_only_to_reference_year() -> None:
    document, annotation = _month_only_document(
        text="El problema comenzó en marzo.",
        predicate_text="comenzó",
        predicate_lemma="comenzar",
        predicate_start=12,
        predicate_end=19,
        predicate_feats="Mood=Ind|Tense=Past|VerbForm=Fin",
        month_start=23,
        month_end=28,
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert (
        annotation.metadata["normalized"]
        == "2025-03-01T00:00:00+01:00"
    )
    assert (
        annotation.metadata["context_resolution"]["rule"]
        == "month_by_predicate_orientation"
    )
    assert (
        annotation.metadata["context_resolution"][
            "temporal_orientation"
        ]
        == "PAST"
    )


def test_keeps_future_month_only_resolution() -> None:
    document, annotation = _month_only_document(
        text="El problema comenzará en marzo.",
        predicate_text="comenzará",
        predicate_lemma="comenzar",
        predicate_start=12,
        predicate_end=21,
        predicate_feats="Mood=Ind|Tense=Fut|VerbForm=Fin",
        month_start=25,
        month_end=30,
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert (
        annotation.metadata["normalized"]
        == "2026-03-01T00:00:00+01:00"
    )
    assert "context_resolution" not in annotation.metadata


def test_resolves_past_month_only_with_hasta() -> None:
    document, annotation = _month_only_document(
        text="La actividad cayó hasta marzo.",
        predicate_text="cayó",
        predicate_lemma="caer",
        predicate_start=13,
        predicate_end=17,
        predicate_feats="Mood=Ind|Tense=Past|VerbForm=Fin",
        month_start=24,
        month_end=29,
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert (
        annotation.metadata["normalized"]
        == "2025-03-01T00:00:00+01:00"
    )
    assert (
        annotation.metadata["context_resolution"]["rule"]
        == "month_by_predicate_orientation"
    )


def test_keeps_future_month_only_with_hasta() -> None:
    document, annotation = _month_only_document(
        text="La actividad continuará hasta marzo.",
        predicate_text="continuará",
        predicate_lemma="continuar",
        predicate_start=13,
        predicate_end=23,
        predicate_feats="Mood=Ind|Tense=Fut|VerbForm=Fin",
        month_start=30,
        month_end=35,
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert (
        annotation.metadata["normalized"]
        == "2026-03-01T00:00:00+01:00"
    )
    assert "context_resolution" not in annotation.metadata


def test_resolves_month_only_with_present_perfect() -> None:
    text = "Desde marzo han aumentado los precios."

    annotation = Annotation(
        start=6,
        end=11,
        text="marzo",
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        subtype="time",
        metadata={
            "grain": "month",
            "normalized": "2026-03-01T00:00:00+01:00",
            "raw_value": {
                "grain": "month",
                "type": "value",
                "value": "2026-03-01T00:00:00+01:00",
            },
        },
    )

    document = Document(
        text=text,
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
                            _word(
                                id=1,
                                text="marzo",
                                start=6,
                                end=11,
                                lemma="marzo",
                                upos="NOUN",
                                head=3,
                                deprel="obl",
                            ),
                            _word(
                                id=2,
                                text="han",
                                start=12,
                                end=15,
                                lemma="haber",
                                upos="AUX",
                                head=3,
                                deprel="aux",
                                feats=(
                                    "Mood=Ind|Tense=Pres|"
                                    "VerbForm=Fin"
                                ),
                            ),
                            _word(
                                id=3,
                                text="aumentado",
                                start=16,
                                end=25,
                                lemma="aumentar",
                                upos="VERB",
                                head=0,
                                deprel="root",
                                feats=(
                                    "Tense=Past|VerbForm=Part"
                                ),
                            ),
                        ],
                    },
                ],
            },
        },
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert (
        annotation.metadata["normalized"]
        == "2025-03-01T00:00:00+01:00"
    )
    assert (
        annotation.metadata["context_resolution"]["rule"]
        == "month_by_predicate_orientation"
    )
    assert (
        annotation.metadata["context_resolution"][
            "temporal_orientation"
        ]
        == "PAST"
    )


def test_keeps_month_only_when_orientation_is_unknown() -> None:
    document, annotation = _month_only_document(
        text="Los datos corresponden a marzo.",
        predicate_text="corresponden",
        predicate_lemma="corresponder",
        predicate_start=10,
        predicate_end=22,
        predicate_feats="Mood=Ind|Tense=Pres|VerbForm=Fin",
        month_start=25,
        month_end=30,
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert (
        annotation.metadata["normalized"]
        == "2026-03-01T00:00:00+01:00"
    )
    assert "context_resolution" not in annotation.metadata

def test_does_not_refine_month_with_explicit_year() -> None:
    text = "El problema comenzó en marzo de 2026."

    annotation = Annotation(
        start=23,
        end=36,
        text="marzo de 2026",
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        subtype="time",
        metadata={
            "grain": "month",
            "normalized": "2026-03-01T00:00:00+01:00",
            "raw_value": {
                "grain": "month",
                "type": "value",
                "value": "2026-03-01T00:00:00+01:00",
            },
        },
    )

    document = Document(
        text=text,
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
                            _word(
                                id=1,
                                text="comenzó",
                                start=12,
                                end=19,
                                lemma="comenzar",
                                upos="VERB",
                                head=0,
                                deprel="root",
                                feats=(
                                    "Mood=Ind|Tense=Past|"
                                    "VerbForm=Fin"
                                ),
                            ),
                            _word(
                                id=2,
                                text="marzo",
                                start=23,
                                end=28,
                                lemma="marzo",
                                upos="PROPN",
                                head=1,
                                deprel="obl",
                            ),
                            _word(
                                id=3,
                                text="2026",
                                start=32,
                                end=36,
                                lemma="2026",
                                upos="NUM",
                                head=2,
                                deprel="nmod",
                                feats="NumForm=Digit|NumType=Card",
                            ),
                        ],
                    },
                ],
            },
        },
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert (
        annotation.metadata["normalized"]
        == "2026-03-01T00:00:00+01:00"
    )
    assert "context_resolution" not in annotation.metadata


def _relative_quantified_time_document(
    *,
    text: str,
    annotation_start: int,
    annotation_end: int,
    annotation_text: str,
    words: list[dict],
) -> tuple[Document, Annotation]:
    annotation = Annotation(
        start=annotation_start,
        end=annotation_end,
        text=annotation_text,
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        subtype="time",
        metadata={
            "grain": "second",
            "normalized": "2025-04-28T23:29:11.000+02:00",
            "raw_value": {
                "grain": "second",
                "type": "value",
                "value": "2025-04-28T23:29:11.000+02:00",
            },
            "duckling_dim": "time",
            "duckling_body": annotation_text,
            "reference_datetime": "2025-04-28T23:24:11+02:00",
            "reference_datetime_source": "source.publication_date",
        },
    )

    document = Document(
        text=text,
        annotations=[annotation],
        metadata={
            "source": {
                "publication_date": "2025-04-28T23:24:11+02:00",
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

    return document, annotation


def test_refines_relative_time_as_duration_with_past_predicate() -> None:
    document, annotation = _relative_quantified_time_document(
        text="España perdió la energía en cinco segundos.",
        annotation_start=25,
        annotation_end=42,
        annotation_text="en cinco segundos",
        words=[
            _word(
                id=1,
                text="España",
                start=0,
                end=6,
                lemma="España",
                upos="PROPN",
                head=2,
                deprel="nsubj",
            ),
            _word(
                id=2,
                text="perdió",
                start=7,
                end=13,
                lemma="perder",
                upos="VERB",
                head=0,
                deprel="root",
                feats="Mood=Ind|Tense=Past|VerbForm=Fin",
            ),
            _word(
                id=3,
                text="cinco",
                start=28,
                end=33,
                lemma="cinco",
                upos="NUM",
                head=4,
                deprel="nummod",
            ),
            _word(
                id=4,
                text="segundos",
                start=34,
                end=42,
                lemma="segundo",
                upos="NOUN",
                head=2,
                deprel="obl",
            ),
        ],
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert annotation.label == "DURATION"
    assert annotation.metadata["resolved_from"] == "DATE"
    assert (
        annotation.metadata["context_resolution"]["rule"]
        == "relative_time_as_elapsed_duration"
    )
    assert (
        annotation.metadata["context_resolution"]["temporal_orientation"]
        == "PAST"
    )

def test_refines_relative_time_as_duration_with_present_perfect() -> None:
    document, annotation = _relative_quantified_time_document(
        text="Ha terminado el trabajo en dos horas.",
        annotation_start=24,
        annotation_end=36,
        annotation_text="en dos horas",
        words=[
            _word(
                id=1,
                text="Ha",
                start=0,
                end=2,
                lemma="haber",
                upos="AUX",
                head=2,
                deprel="aux",
                feats="Mood=Ind|Tense=Pres|VerbForm=Fin",
            ),
            _word(
                id=2,
                text="terminado",
                start=3,
                end=12,
                lemma="terminar",
                upos="VERB",
                head=0,
                deprel="root",
                feats="Tense=Past|VerbForm=Part",
            ),
            _word(
                id=3,
                text="dos",
                start=27,
                end=30,
                lemma="dos",
                upos="NUM",
                head=4,
                deprel="nummod",
            ),
            _word(
                id=4,
                text="horas",
                start=31,
                end=36,
                lemma="hora",
                upos="NOUN",
                head=2,
                deprel="obl",
            ),
        ],
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert annotation.label == "DURATION"
    assert annotation.metadata["resolved_from"] == "DATE"


def test_refines_relative_time_as_duration_with_past_perfect() -> None:
    document, annotation = _relative_quantified_time_document(
        text="Había terminado el trabajo en dos horas.",
        annotation_start=27,
        annotation_end=39,
        annotation_text="en dos horas",
        words=[
            _word(
                id=1,
                text="Había",
                start=0,
                end=5,
                lemma="haber",
                upos="AUX",
                head=2,
                deprel="aux",
                feats="Mood=Ind|Tense=Imp|VerbForm=Fin",
            ),
            _word(
                id=2,
                text="terminado",
                start=6,
                end=15,
                lemma="terminar",
                upos="VERB",
                head=0,
                deprel="root",
                feats="Tense=Past|VerbForm=Part",
            ),
            _word(
                id=3,
                text="dos",
                start=30,
                end=33,
                lemma="dos",
                upos="NUM",
                head=4,
                deprel="nummod",
            ),
            _word(
                id=4,
                text="horas",
                start=34,
                end=39,
                lemma="hora",
                upos="NOUN",
                head=2,
                deprel="obl",
            ),
        ],
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert annotation.label == "DURATION"
    assert annotation.metadata["resolved_from"] == "DATE"


def test_keeps_relative_time_as_date_with_future_predicate() -> None:
    document, annotation = _relative_quantified_time_document(
        text="Volverá en dos horas.",
        annotation_start=8,
        annotation_end=20,
        annotation_text="en dos horas",
        words=[
            _word(
                id=1,
                text="Volverá",
                start=0,
                end=7,
                lemma="volver",
                upos="VERB",
                head=0,
                deprel="root",
                feats="Mood=Ind|Tense=Fut|VerbForm=Fin",
            ),
            _word(
                id=2,
                text="horas",
                start=15,
                end=20,
                lemma="hora",
                upos="NOUN",
                head=1,
                deprel="obl",
            ),
        ],
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert annotation.label == "DATE"
    assert "context_resolution" not in annotation.metadata


def test_keeps_relative_time_as_date_with_conditional_predicate() -> None:
    document, annotation = _relative_quantified_time_document(
        text="Dijo que volvería en cinco minutos.",
        annotation_start=18,
        annotation_end=34,
        annotation_text="en cinco minutos",
        words=[
            _word(
                id=1,
                text="Dijo",
                start=0,
                end=4,
                lemma="decir",
                upos="VERB",
                head=0,
                deprel="root",
                feats="Mood=Ind|Tense=Past|VerbForm=Fin",
            ),
            _word(
                id=2,
                text="volvería",
                start=9,
                end=17,
                lemma="volver",
                upos="VERB",
                head=1,
                deprel="ccomp",
                feats="Mood=Cnd|VerbForm=Fin",
            ),
            _word(
                id=3,
                text="minutos",
                start=27,
                end=34,
                lemma="minuto",
                upos="NOUN",
                head=2,
                deprel="obl",
            ),
        ],
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert annotation.label == "DATE"
    assert "context_resolution" not in annotation.metadata


def test_keeps_relative_time_bound_to_local_future_predicate() -> None:
    document, annotation = _relative_quantified_time_document(
        text="Ayer dijo que volverá en dos horas.",
        annotation_start=22,
        annotation_end=34,
        annotation_text="en dos horas",
        words=[
            _word(
                id=1,
                text="dijo",
                start=5,
                end=9,
                lemma="decir",
                upos="VERB",
                head=0,
                deprel="root",
                feats="Mood=Ind|Tense=Past|VerbForm=Fin",
            ),
            _word(
                id=2,
                text="volverá",
                start=14,
                end=21,
                lemma="volver",
                upos="VERB",
                head=1,
                deprel="ccomp",
                feats="Mood=Ind|Tense=Fut|VerbForm=Fin",
            ),
            _word(
                id=3,
                text="horas",
                start=29,
                end=34,
                lemma="hora",
                upos="NOUN",
                head=2,
                deprel="obl",
            ),
        ],
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert annotation.label == "DATE"
    assert "context_resolution" not in annotation.metadata


def test_does_not_refine_non_quantified_en_time_as_duration() -> None:
    document, annotation = _relative_quantified_time_document(
        text="El problema ocurrió en verano.",
        annotation_start=20,
        annotation_end=30,
        annotation_text="en verano",
        words=[
            _word(
                id=1,
                text="problema",
                start=3,
                end=11,
                lemma="problema",
                upos="NOUN",
                head=2,
                deprel="nsubj",
            ),
            _word(
                id=2,
                text="ocurrió",
                start=12,
                end=19,
                lemma="ocurrir",
                upos="VERB",
                head=0,
                deprel="root",
                feats="Mood=Ind|Tense=Past|VerbForm=Fin",
            ),
            _word(
                id=3,
                text="verano",
                start=23,
                end=30,
                lemma="verano",
                upos="NOUN",
                head=2,
                deprel="obl",
            ),
        ],
    )

    TemporalContextEnricher(language="es").enrich(document)

    assert annotation.label == "DATE"
    assert "context_resolution" not in annotation.metadata