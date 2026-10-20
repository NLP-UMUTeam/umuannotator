from umuannotator.document.model import (
    Annotation,
    Document,
    Relation,
    RelationArgument,
    RelationPredicate,
)
from umuannotator.serialization.documents import (
    deserialize_document,
    serialize_document,
)


def test_document_roundtrip():
    document = Document(
        text="El Gobierno anuncia ayudas.",
        metadata={
            "doc_id": "doc-1",
        },
        annotations=[
            Annotation(
                start=3,
                end=11,
                text="Gobierno",
                label="Government",
                layer="ontology",
                source="ontology",
                score=0.75,
                metadata={
                    "concept_id": (
                        "http://example.org/Government"
                    )
                },
            )
        ],
        relations=[
            Relation(
                id="rel-1",
                type="predicate_argument",
                source="stanza",
                predicate=RelationPredicate(
                    start=12,
                    end=19,
                    text="anuncia",
                    lemma="anunciar",
                ),
                arguments=[
                    RelationArgument(
                        role="subject",
                        start=3,
                        end=11,
                        text="Gobierno",
                        annotation_id="ann-1",
                    )
                ],
                metadata={
                    "confidence": 1.0,
                },
            )
        ],
    )

    serialized = serialize_document(
        document,
        output_profile="full",
    )

    restored = deserialize_document(
        serialized
    )

    serialized_again = serialize_document(
        restored,
        output_profile="full",
    )

    assert serialized_again == serialized