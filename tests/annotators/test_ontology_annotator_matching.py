from umuannotator.annotators.ontology import OntologyAnnotator
from umuannotator.document import Document
from umuannotator.ontology.model import Concept

def make_concept(**kwargs):
    concept = Concept(
        uri="http://example.org#Pizza",
        name="Pizza",
        entity_type="owl:Class",
    )

    for key, value in kwargs.items():
        setattr(concept, key, value)

    return concept


def test_matches_labels_case_insensitive():
    concept = make_concept(
        labels=["Pizza"],
    )

    annotator = OntologyAnnotator(
        concepts={concept.uri: concept},
    )

    document = Document(
        text="I love PIZZA."
    )

    annotator.annotate(document)

    assert len(document.annotations) == 1
    assert document.annotations[0].text == "PIZZA"
    assert document.annotations[0].metadata["match_source"] == "label"


def test_matches_aliases():
    concept = make_concept(
        aliases=["pie"],
    )

    annotator = OntologyAnnotator(
        concepts={concept.uri: concept},
    )

    document = Document(
        text="I love pie."
    )

    annotator.annotate(document)

    assert len(document.annotations) == 1
    assert document.annotations[0].text == "pie"
    assert document.annotations[0].metadata["match_source"] == "alias"


def test_matches_regex_patterns():
    concept = make_concept(
        patterns=[r"pizza(s)?"],
    )

    annotator = OntologyAnnotator(
        concepts={concept.uri: concept},
    )

    document = Document(
        text="Two pizzas please."
    )

    annotator.annotate(document)

    assert len(document.annotations) == 1
    assert document.annotations[0].text == "pizzas"
    assert document.annotations[0].metadata["match_source"] == "regex"


def test_does_not_match_name_by_default():
    concept = make_concept(
        name="PepperoniPizza",
    )

    annotator = OntologyAnnotator(
        concepts={concept.uri: concept},
    )

    document = Document(
        text="Pepperoni Pizza"
    )

    annotator.annotate(document)

    assert document.annotations == []


def test_matches_name_when_enabled():
    concept = make_concept(
        name="Pepperoni",
    )

    annotator = OntologyAnnotator(
        concepts={concept.uri: concept},
        matching_config={
            "fields": {
                "name": True,
            }
        },
    )

    document = Document(
        text="Pepperoni"
    )

    annotator.annotate(document)

    assert len(document.annotations) == 1
    assert document.annotations[0].metadata["match_source"] == "name"


def test_matches_camel_case_name():
    concept = make_concept(
        name="PepperoniPizza",
    )

    annotator = OntologyAnnotator(
        concepts={concept.uri: concept},
        matching_config={
            "fields": {
                "name": True,
                "name_camel_case": True,
            }
        },
    )

    document = Document(
        text="Pepperoni Pizza"
    )

    annotator.annotate(document)

    assert len(document.annotations) == 1

    annotation = document.annotations[0]

    assert annotation.text == "Pepperoni Pizza"
    assert annotation.metadata["match_source"] == "name_camel_case"
    assert annotation.metadata["matched_value"] == "Pepperoni Pizza"


def test_does_not_match_camel_case_when_disabled():
    concept = make_concept(
        name="PepperoniPizza",
    )

    annotator = OntologyAnnotator(
        concepts={concept.uri: concept},
        matching_config={
            "fields": {
                "name": True,
                "name_camel_case": False,
            }
        },
    )

    document = Document(
        text="Pepperoni Pizza"
    )

    annotator.annotate(document)

    assert document.annotations == []


def test_annotation_contains_matching_metadata():
    concept = make_concept(
        labels=["Pizza"],
    )

    annotator = OntologyAnnotator(
        concepts={concept.uri: concept},
    )

    document = Document(
        text="Pizza"
    )

    annotator.annotate(document)

    metadata = document.annotations[0].metadata

    assert metadata["match_source"] == "label"
    assert metadata["matched_value"] == "Pizza"
    assert metadata["concept_uri"] == concept.uri


def test_literal_terms_use_word_boundaries():
    concept = make_concept(
        labels=["Pizza"],
    )

    annotator = OntologyAnnotator(
        concepts={concept.uri: concept},
    )

    document = Document(
        text="Pizzazz is not pizza."
    )

    annotator.annotate(document)

    assert len(document.annotations) == 1
    assert document.annotations[0].text == "pizza"


def test_duplicate_label_and_regex_currently_create_two_annotations():
    concept = make_concept(
        labels=["Pizza"],
        patterns=[r"pizza"],
    )

    annotator = OntologyAnnotator(
        concepts={concept.uri: concept},
    )

    document = Document(
        text="Pizza"
    )

    annotator.annotate(document)

    assert len(document.annotations) == 2

    match_sources = {
        annotation.metadata["match_source"]
        for annotation in document.annotations
    }

    assert match_sources == {"label", "regex"}


def test_overlapping_label_and_camel_case_currently_create_two_annotations():
    concept = make_concept(
        labels=["Pepperoni Pizza"],
        name="PepperoniPizza",
    )

    annotator = OntologyAnnotator(
        concepts={concept.uri: concept},
        matching_config={
            "fields": {
                "labels": True,
                "name": True,
                "name_camel_case": True,
            }
        },
    )

    document = Document(
        text="Pepperoni Pizza"
    )

    annotator.annotate(document)

    assert len(document.annotations) == 2

    match_sources = {
        annotation.metadata["match_source"]
        for annotation in document.annotations
    }

    assert match_sources == {"label", "name_camel_case"}