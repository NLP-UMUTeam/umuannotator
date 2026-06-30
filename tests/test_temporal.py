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