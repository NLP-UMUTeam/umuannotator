from umuannotator.annotators.temporal import TemporalAnnotator, is_bad_temporal_surface
from umuannotator.document.model import Annotation, Document
from umuannotator.lang.temporal import get_temporal_rules

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


def test_filters_bad_single_temporal_surface():
    assert is_bad_temporal_surface("una")
    assert is_bad_temporal_surface("un")
    assert is_bad_temporal_surface("unos")
    assert is_bad_temporal_surface("ya")
    assert is_bad_temporal_surface("ahora")
    assert is_bad_temporal_surface("primero")
    assert is_bad_temporal_surface("mar")


def test_filters_bad_preposition_plus_single_surface():
    assert is_bad_temporal_surface("en una")
    assert is_bad_temporal_surface("de un")
    assert is_bad_temporal_surface("para uno")


def test_keeps_valid_temporal_surface():
    assert not is_bad_temporal_surface("mañana")
    assert not is_bad_temporal_surface("el lunes")
    assert not is_bad_temporal_surface("en 2024")
    assert not is_bad_temporal_surface("durante una semana")
    assert not is_bad_temporal_surface("hoy", grain="day")
    assert not is_bad_temporal_surface("Navidad", grain="day")
    assert not is_bad_temporal_surface("julio", grain="month")
    assert not is_bad_temporal_surface("2025", grain="year")
    assert not is_bad_temporal_surface("24 horas", dim="duration")
    assert not is_bad_temporal_surface("10 años", dim="duration")


def test_filters_bare_numeric_duration():
    assert is_bad_temporal_surface("3", dim="duration")


def test_filters_bad_year_surfaces_only_when_grain_is_year():
    assert is_bad_temporal_surface("mil", grain="year")
    assert is_bad_temporal_surface("1.000", grain="year")
    assert is_bad_temporal_surface("1000", grain="year")
    assert is_bad_temporal_surface("2.000", grain="year")

    assert not is_bad_temporal_surface("mil")
    assert not is_bad_temporal_surface("1.000")


def test_filters_a_plus_time_word():
    assert is_bad_temporal_surface("a cuatro")
    assert is_bad_temporal_surface("a cinco")


def test_filters_un_minute_expression():
    assert is_bad_temporal_surface("un 30", grain="minute")


def test_temporal_filters_julio_inside_person_entity():
    annotator = TemporalAnnotator(language="es")

    document = Document(text="Julio Iglesias actuará mañana.")
    document.metadata["stanza"] = {
        "entities": [
            {
                "text": "Julio Iglesias",
                "type": "PER",
                "start": 0,
                "end": 15,
            }
        ]
    }

    annotation = Annotation(
        start=0,
        end=5,
        text="Julio",
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        metadata={},
    )

    assert annotator._is_false_positive_person_name(annotation, document)


def test_temporal_keeps_julio_when_not_inside_person_entity():
    annotator = TemporalAnnotator(language="es")

    document = Document(text="El empleo sube en julio.")
    document.metadata["stanza"] = {
        "entities": []
    }

    annotation = Annotation(
        start=18,
        end=23,
        text="julio",
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        metadata={},
    )

    assert not annotator._is_false_positive_person_name(annotation, document)


def test_temporal_keeps_julio_without_stanza_metadata():
    annotator = TemporalAnnotator(language="es")

    document = Document(text="El empleo sube en julio.")

    annotation = Annotation(
        start=18,
        end=23,
        text="julio",
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        metadata={},
    )

    assert not annotator._is_false_positive_person_name(annotation, document)


def test_temporal_does_not_filter_julio_inside_non_person_entity():
    annotator = TemporalAnnotator(language="es")

    document = Document(text="Barcelona tendrá obras en julio.")
    document.metadata["stanza"] = {
        "entities": [
            {
                "text": "Barcelona",
                "type": "LOC",
                "start": 0,
                "end": 9,
            }
        ]
    }

    annotation = Annotation(
        start=25,
        end=30,
        text="julio",
        label="DATE",
        layer="temporal",
        source="duckling-temporal",
        type="temporal",
        metadata={},
    )

    assert not annotator._is_false_positive_person_name(annotation, document)


def test_temporal_loads_spanish_rules():
    rules = get_temporal_rules("es")

    assert "ahora" in rules.bad_single_words
    assert "mar" in rules.bad_single_words
    assert "mil" in rules.bad_year_surfaces
    assert "julio" in rules.person_name_month_words
    assert "SEP" in rules.bad_exact_surfaces
    assert rules.clock_time_only_patterns == (
        r"^\d{1,2}:\d{2}$",
        r"^a las \d{1,2}:\d{2}$",
        r"^a la \d{1,2}:\d{2}$",
    )


def test_temporal_unknown_language_uses_empty_rules():
    rules = get_temporal_rules("xx")

    assert rules.bad_exact_surfaces == set()
    assert rules.bad_starts == set()
    assert rules.bad_single_words == set()
    assert rules.bad_prepositional_time_starts == set()
    assert rules.bad_prepositional_time_words == set()
    assert rules.bad_year_surfaces == set()
    assert rules.bad_prefixes_by_grain == {}
    assert rules.person_name_month_words == set()
    assert rules.clock_time_only_patterns == ()


def test_temporal_bad_surface_can_use_explicit_rules():
    rules = get_temporal_rules("es")

    assert is_bad_temporal_surface(
        "ahora",
        rules=rules,
    )


def test_temporal_loads_spanish_bad_prefixes_by_grain():
    rules = get_temporal_rules("es")

    assert rules.bad_prefixes_by_grain["minute"] == ("un ",)


def test_temporal_empty_rules_do_not_filter_spanish_specific_cases():
    rules = get_temporal_rules("xx")

    assert not is_bad_temporal_surface(
        "a cuatro",
        rules=rules,
    )

    assert not is_bad_temporal_surface(
        "un 30",
        grain="minute",
        rules=rules,
    )


def test_temporal_filters_bad_exact_surface_sep():
    assert is_bad_temporal_surface("SEP")


def test_temporal_does_not_filter_lowercase_sep_as_exact_surface():
    assert not is_bad_temporal_surface("sep")


def test_temporal_uses_reference_datetime_from_metadata():
    document = Document(
        text="Ayer ocurrió el incidente.",
        metadata={
            "source": {
                "publication_date": (
                    "2025-04-29T10:00:00+02:00"
                ),
            }
        },
    )

    annotator = TemporalAnnotator(
        language="es",
        reference_datetime_metadata_key=(
            "source.publication_date"
        ),
    )

    reference_datetime, source = (
        annotator._resolve_reference_datetime(
            document
        )
    )

    assert (
        reference_datetime.year,
        reference_datetime.month,
        reference_datetime.day,
    ) == (
        2025,
        4,
        29,
    )

    assert source == (
        "source.publication_date"
    )


def test_temporal_reference_metadata_path():
    document = Document(
        text="Texto.",
        metadata={
            "source": {
                "publication_date": (
                    "2024-06-15"
                ),
            }
        },
    )

    annotator = TemporalAnnotator(
        reference_datetime_metadata_key=(
            "source.publication_date"
        ),
    )

    value = annotator._get_metadata_value(
        document.metadata,
        "source.publication_date",
    )

    assert value == "2024-06-15"


def test_temporal_ayer_uses_document_reference_date():
    document = Document(
        text="El Gobierno anunció ayer nuevas medidas.",
        metadata={
            "source": {
                "publication_date": (
                    "2025-04-29T10:00:00+02:00"
                ),
            }
        },
    )

    annotator = TemporalAnnotator(
        language="es",
        reference_datetime_metadata_key=(
            "source.publication_date"
        ),
    )

    result = annotator.annotate(
        document
    )

    ayer = next(
        annotation
        for annotation in result.annotations
        if annotation.text.lower() == "ayer"
    )

    assert ayer.metadata[
        "normalized"
    ].startswith(
        "2025-04-28"
    )

    assert ayer.metadata[
        "reference_datetime"
    ].startswith(
        "2025-04-29T10:00:00"
    )

    assert ayer.metadata[
        "reference_datetime_source"
    ] == "source.publication_date"

def test_temporal_clock_time_only_is_unresolved_time():
    result = annotate("El apagón comenzó a las 12:33.")

    annotation = assert_annotation(
        result,
        text="a las 12:33",
        label="TIME",
    )

    assert annotation.metadata["normalized"] == "12:33"
    assert annotation.metadata["date_resolved"] is False
    assert annotation.metadata["grain"] == "minute"
    assert annotation.metadata["duckling_dim"] == "time"


def test_temporal_bare_clock_time_is_unresolved_time():
    result = annotate("El apagón comenzó 12:33.")

    annotation = assert_annotation(
        result,
        text="12:33",
        label="TIME",
    )

    assert annotation.metadata["normalized"] == "12:33"
    assert annotation.metadata["date_resolved"] is False


def test_temporal_explicit_date_and_time_remains_date():
    result = annotate(
        "El apagón comenzó el 28 de abril a las 12:33."
    )

    annotation = assert_annotation(
        result,
        text="el 28 de abril a las 12:33",
        label="DATE",
    )

    assert annotation.metadata["normalized"] != "12:33"
    assert "date_resolved" not in annotation.metadata


def test_temporal_relative_date_and_time_remains_date():
    result = annotate(
        "El apagón comenzó ayer a las 12:33."
    )

    annotation = assert_annotation(
        result,
        text="ayer a las 12:33",
        label="DATE",
    )

    assert annotation.metadata["normalized"] != "12:33"
    assert "date_resolved" not in annotation.metadata


def test_temporal_weekday_and_time_remains_date():
    result = annotate(
        "El apagón comenzó el lunes a las 12:33."
    )

    annotation = assert_annotation(
        result,
        text="el lunes a las 12:33",
        label="DATE",
    )

    assert annotation.metadata["normalized"] != "12:33"
    assert "date_resolved" not in annotation.metadata

def test_temporal_date_with_clock_selects_matching_candidate():
    result = annotate(
        "El apagón comenzó ayer a las 08:30."
    )

    annotation = assert_annotation(
        result,
        text="ayer a las 08:30",
        label="DATE",
    )

    assert "T08:30:00" in annotation.metadata["normalized"]


def test_temporal_date_with_noon_clock_selects_12_not_00():
    result = annotate(
        "El apagón comenzó ayer a las 12:33."
    )

    annotation = assert_annotation(
        result,
        text="ayer a las 12:33",
        label="DATE",
    )

    normalized = annotation.metadata["normalized"]

    assert "T12:33:00" in normalized
    assert "T00:33:00" not in normalized

def test_rejects_temporal_date_followed_by_percent_sign():
    document = Document(
        text="El 26% considera que habrá un ciberataque.",
    )

    annotator = TemporalAnnotator(language="es")

    result = {
        "dim": "time",
        "body": "El 26",
        "start": 0,
        "end": 5,
        "value": {
            "type": "value",
            "grain": "day",
            "value": "2026-10-26T00:00:00.000+01:00",
        },
    }

    annotation = annotator.result_to_annotation(document, result)

    assert annotation is None


def test_keeps_temporal_day_without_percent_sign():
    document = Document(
        text="El 26 llegaron los primeros participantes.",
    )

    annotator = TemporalAnnotator(language="es")

    result = {
        "dim": "time",
        "body": "El 26",
        "start": 0,
        "end": 5,
        "value": {
            "type": "value",
            "grain": "day",
            "value": "2026-10-26T00:00:00.000+01:00",
        },
    }

    annotation = annotator.result_to_annotation(document, result)

    assert annotation is not None
    assert annotation.label == "DATE"


def test_keeps_temporal_date_with_month():
    document = Document(
        text="El 26 de abril ocurrió el apagón.",
    )

    annotator = TemporalAnnotator(language="es")

    result = {
        "dim": "time",
        "body": "El 26 de abril",
        "start": 0,
        "end": 14,
        "value": {
            "type": "value",
            "grain": "day",
            "value": "2027-04-26T00:00:00.000+02:00",
        },
    }

    annotation = annotator.result_to_annotation(document, result)

    assert annotation is not None
    assert annotation.label == "DATE"