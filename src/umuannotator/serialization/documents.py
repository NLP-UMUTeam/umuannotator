from __future__ import annotations

from typing import Any

from umuannotator.document.model import (
    Annotation,
    Document,
    Relation,
    RelationArgument,
    RelationPredicate,
)
from umuannotator.renderers.json import document_to_dict
from umuannotator.serialization.profiles import apply_output_profile


def serialize_document(
    document: Document,
    *,
    output_profile: str = "compact",
) -> dict[str, Any]:
    data = {
        "documents": [
            document_to_dict(document),
        ],
        "metadata": {},
    }

    serialized = apply_output_profile(
        data,
        profile=output_profile,
    )

    return serialized["documents"][0]


def deserialize_annotation(
    data: dict[str, Any],
) -> Annotation:
    return Annotation(
        start=data["start"],
        end=data["end"],
        text=data["text"],
        label=data["label"],
        layer=data["layer"],
        source=data.get("source"),
        type=data.get("type"),
        subtype=data.get("subtype"),
        score=data.get("score"),
        metadata=dict(
            data.get("metadata") or {}
        ),
    )


def deserialize_relation_predicate(
    data: dict[str, Any],
) -> RelationPredicate:
    return RelationPredicate(
        start=data["start"],
        end=data["end"],
        text=data["text"],
        lemma=data.get("lemma"),
        metadata=dict(
            data.get("metadata") or {}
        ),
    )


def deserialize_relation_argument(
    data: dict[str, Any],
) -> RelationArgument:
    return RelationArgument(
        role=data["role"],
        start=data["start"],
        end=data["end"],
        text=data["text"],
        annotation_id=data.get(
            "annotation_id"
        ),
        annotations=list(
            data.get("annotations") or []
        ),
        metadata=dict(
            data.get("metadata") or {}
        ),
    )


def deserialize_relation(
    data: dict[str, Any],
) -> Relation:
    return Relation(
        id=data.get("id"),
        type=data["type"],
        predicate=(
            deserialize_relation_predicate(
                data["predicate"]
            )
        ),
        arguments=[
            deserialize_relation_argument(
                argument
            )
            for argument in data.get(
                "arguments",
                [],
            )
        ],
        source=data.get("source"),
        score=data.get("score"),
        metadata=dict(
            data.get("metadata") or {}
        ),
    )


def deserialize_document(
    data: dict[str, Any],
) -> Document:
    return Document(
        text=data["text"],
        metadata=dict(
            data.get("metadata") or {}
        ),
        annotations=[
            deserialize_annotation(annotation)
            for annotation in data.get(
                "annotations",
                [],
            )
        ],
        relations=[
            deserialize_relation(relation)
            for relation in data.get(
                "relations",
                [],
            )
        ],
    )