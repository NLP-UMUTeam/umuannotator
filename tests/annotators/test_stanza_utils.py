from umuannotator.annotators.stanza_utils import (
    find_stanza_entity_containing,
    find_stanza_token,
)
from umuannotator.document import Document


def test_find_stanza_token_returns_matching_token_by_offsets():
    document = Document(text="un pueblo")

    document.metadata["stanza"] = {
        "tokens": [
            {
                "text": "un",
                "start": 0,
                "end": 2,
                "upos": "DET",
            },
            {
                "text": "pueblo",
                "start": 3,
                "end": 9,
                "upos": "NOUN",
            },
        ]
    }

    token = find_stanza_token(
        document,
        start=0,
        end=2,
    )

    assert token is not None
    assert token["text"] == "un"
    assert token["upos"] == "DET"


def test_find_stanza_token_returns_none_without_stanza_metadata():
    document = Document(text="un pueblo")

    token = find_stanza_token(
        document,
        start=0,
        end=2,
    )

    assert token is None


def test_find_stanza_token_returns_none_when_offsets_do_not_match():
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

    token = find_stanza_token(
        document,
        start=0,
        end=2,
    )

    assert token is None


def test_find_stanza_entity_containing_returns_entity_for_exact_span():
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

    entity = find_stanza_entity_containing(
        document,
        start=0,
        end=15,
    )

    assert entity is not None
    assert entity["text"] == "Julio Iglesias"
    assert entity["type"] == "PER"


def test_find_stanza_entity_containing_returns_entity_for_inner_span():
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

    entity = find_stanza_entity_containing(
        document,
        start=0,
        end=5,
    )

    assert entity is not None
    assert entity["text"] == "Julio Iglesias"


def test_find_stanza_entity_containing_returns_none_without_stanza_metadata():
    document = Document(text="Julio Iglesias actuará mañana.")

    entity = find_stanza_entity_containing(
        document,
        start=0,
        end=5,
    )

    assert entity is None


def test_find_stanza_entity_containing_returns_none_when_no_entity_contains_span():
    document = Document(text="Julio Iglesias actuará mañana.")

    document.metadata["stanza"] = {
        "entities": [
            {
                "text": "mañana",
                "type": "DATE",
                "start": 24,
                "end": 30,
            }
        ]
    }

    entity = find_stanza_entity_containing(
        document,
        start=0,
        end=5,
    )

    assert entity is None


def test_find_stanza_entity_containing_ignores_entities_without_offsets():
    document = Document(text="Julio Iglesias actuará mañana.")

    document.metadata["stanza"] = {
        "entities": [
            {
                "text": "Julio Iglesias",
                "type": "PER",
            }
        ]
    }

    entity = find_stanza_entity_containing(
        document,
        start=0,
        end=5,
    )

    assert entity is None