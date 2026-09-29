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
