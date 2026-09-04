from umuannotator.document import (
    Document,
    Relation,
    RelationArgument,
    RelationPredicate,
)
from umuannotator.serialization.documents import (
    serialize_document,
)


def build_document_with_relation():
    document = Document(
        text="El Gobierno anuncia ayudas."
    )

    document.add_relation(
        Relation(
            id="rel-1",
            type="predicate_argument",
            predicate=RelationPredicate(
                start=12,
                end=19,
                text="anuncia",
                lemma="anunciar",
                metadata={
                    "word_id": 3,
                },
            ),
            arguments=[
                RelationArgument(
                    role="subject",
                    start=0,
                    end=11,
                    text="El Gobierno",
                    metadata={
                        "head_word_id": 2,
                    },
                ),
                RelationArgument(
                    role="object",
                    start=20,
                    end=26,
                    text="ayudas",
                    metadata={
                        "head_word_id": 4,
                    },
                ),
            ],
            source="stanza-dependency",
            metadata={
                "sentence_id": 0,
                "rule": "verb_nsubj_obj",
            },
        )
    )

    return document

def test_serialize_relation_full():
    document = build_document_with_relation()

    result = serialize_document(
        document,
        output_profile="full",
    )

    assert len(result["relations"]) == 1

    relation = result["relations"][0]

    assert relation["id"] == "rel-1"
    assert relation["predicate"]["lemma"] == "anunciar"
    assert relation["arguments"][0]["role"] == "subject"

    assert relation["metadata"]["sentence_id"] == 0
    assert relation["predicate"]["metadata"]["word_id"] == 3

def test_serialize_relation_compact():
    document = build_document_with_relation()

    result = serialize_document(
        document,
        output_profile="compact",
    )

    relation = result["relations"][0]

    assert relation == {
        "id": "rel-1",
        "type": "predicate_argument",
        "predicate": {
            "start": 12,
            "end": 19,
            "text": "anuncia",
            "lemma": "anunciar",
        },
        "arguments": [
            {
                "role": "subject",
                "start": 0,
                "end": 11,
                "text": "El Gobierno",
            },
            {
                "role": "object",
                "start": 20,
                "end": 26,
                "text": "ayudas",
            },
        ],
        "source": "stanza-dependency",
    }