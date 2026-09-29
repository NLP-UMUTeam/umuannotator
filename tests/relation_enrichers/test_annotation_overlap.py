from __future__ import annotations

from umuannotator.document import (
    Annotation,
    Document,
    Relation,
    RelationArgument,
    RelationPredicate,
)
from umuannotator.relation_enrichers import (
    AnnotationOverlapRelationEnricher,
)


def build_relation(
    argument: RelationArgument,
) -> Relation:
    return Relation(
        type="predicate_argument",
        predicate=RelationPredicate(
            start=7,
            end=13,
            text="perdió",
            lemma="perder",
        ),
        arguments=[
            argument,
        ],
        source="test",
    )


def test_exact_annotation_match():
    argument = RelationArgument(
        role="subject",
        start=0,
        end=6,
        text="España",
    )

    annotation = Annotation(
        start=0,
        end=6,
        text="España",
        label="COUNTRY",
        layer="entity",
        source="test",
    )

    document = Document(
        text="España perdió energía.",
        annotations=[
            annotation,
        ],
        relations=[
            build_relation(argument),
        ],
    )

    enricher = AnnotationOverlapRelationEnricher()

    result = enricher.enrich(document)

    annotations = (
        result.relations[0]
        .arguments[0]
        .annotations
    )

    assert len(annotations) == 1
    assert annotations[0]["text"] == "España"
    assert annotations[0]["label"] == "COUNTRY"
    assert annotations[0]["layer"] == "entity"
    assert annotations[0]["match"] == "exact"


def test_contained_annotation_match():
    argument = RelationArgument(
        role="object",
        start=0,
        end=31,
        text="el equivalente al 60% de la luz",
    )

    annotation = Annotation(
        start=18,
        end=20,
        text="60",
        label="NUMBER",
        layer="quantity",
        source="duckling-quantity",
        metadata={
            "normalized": 60,
        },
    )

    document = Document(
        text="el equivalente al 60% de la luz",
        annotations=[
            annotation,
        ],
        relations=[
            build_relation(argument),
        ],
    )

    enricher = AnnotationOverlapRelationEnricher()

    result = enricher.enrich(document)

    annotations = (
        result.relations[0]
        .arguments[0]
        .annotations
    )

    assert len(annotations) == 1
    assert annotations[0]["text"] == "60"
    assert annotations[0]["match"] == "contained"
    assert annotations[0]["metadata"]["normalized"] == 60


def test_partial_overlap_is_not_matched():
    argument = RelationArgument(
        role="object",
        start=10,
        end=20,
        text="abcdefghij",
    )

    annotation = Annotation(
        start=15,
        end=25,
        text="partial",
        label="TEST",
        layer="test",
    )

    document = Document(
        text="x" * 30,
        annotations=[
            annotation,
        ],
        relations=[
            build_relation(argument),
        ],
    )

    enricher = AnnotationOverlapRelationEnricher()

    result = enricher.enrich(document)

    assert (
        result.relations[0]
        .arguments[0]
        .annotations
        == []
    )


def test_multiple_annotations_can_enrich_same_argument():
    argument = RelationArgument(
        role="object",
        start=0,
        end=25,
        text="España perdió un 60%",
    )

    annotations = [
        Annotation(
            start=0,
            end=6,
            text="España",
            label="COUNTRY",
            layer="entity",
        ),
        Annotation(
            start=18,
            end=20,
            text="60",
            label="NUMBER",
            layer="quantity",
        ),
    ]

    document = Document(
        text="España perdió un 60%",
        annotations=annotations,
        relations=[
            build_relation(argument),
        ],
    )

    enricher = AnnotationOverlapRelationEnricher()

    result = enricher.enrich(document)

    enriched = (
        result.relations[0]
        .arguments[0]
        .annotations
    )

    assert len(enriched) == 2

    assert {
        annotation["layer"]
        for annotation in enriched
    } == {
        "entity",
        "quantity",
    }


def test_no_annotations_leaves_argument_empty():
    argument = RelationArgument(
        role="subject",
        start=0,
        end=6,
        text="España",
    )

    document = Document(
        text="España perdió energía.",
        relations=[
            build_relation(argument),
        ],
    )

    enricher = AnnotationOverlapRelationEnricher()

    result = enricher.enrich(document)

    assert (
        result.relations[0]
        .arguments[0]
        .annotations
        == []
    )