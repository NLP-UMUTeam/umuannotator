from umuannotator.document import (
    Document,
    Relation,
    RelationArgument,
    RelationPredicate,
)


def test_document_has_empty_relations_by_default():
    document = Document(
        text="El Gobierno anuncia ayudas."
    )

    assert document.relations == []


def test_document_can_add_relation():
    document = Document(
        text="El Gobierno anuncia ayudas."
    )

    predicate = RelationPredicate(
        start=12,
        end=19,
        text="anuncia",
        lemma="anunciar",
    )

    subject = RelationArgument(
        role="subject",
        start=0,
        end=11,
        text="El Gobierno",
    )

    object_ = RelationArgument(
        role="object",
        start=20,
        end=26,
        text="ayudas",
    )

    relation = Relation(
        type="predicate_argument",
        predicate=predicate,
        arguments=[
            subject,
            object_,
        ],
        source="stanza-dependency",
    )

    document.add_relation(relation)

    assert len(document.relations) == 1

    result = document.relations[0]

    assert result.type == "predicate_argument"
    assert result.source == "stanza-dependency"

    assert result.predicate.text == "anuncia"
    assert result.predicate.lemma == "anunciar"

    assert len(result.arguments) == 2

    assert result.arguments[0].role == "subject"
    assert result.arguments[0].text == "El Gobierno"

    assert result.arguments[1].role == "object"
    assert result.arguments[1].text == "ayudas"


def test_relation_metadata_is_independent():
    first = Relation(
        type="predicate_argument",
        predicate=RelationPredicate(
            start=0,
            end=7,
            text="anuncia",
        ),
    )

    second = Relation(
        type="predicate_argument",
        predicate=RelationPredicate(
            start=0,
            end=7,
            text="anuncia",
        ),
    )

    first.metadata["rule"] = "verb_nsubj_obj"

    assert "rule" not in second.metadata