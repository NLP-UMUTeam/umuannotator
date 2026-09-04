from __future__ import annotations

from copy import deepcopy
from typing import Any


COMPACT_DOCUMENT_METADATA_KEYS = {
    "doc_id",
}

COMPACT_ANNOTATION_KEYS = {
    "start",
    "end",
    "text",
    "label",
    "layer",
    "source",
    "type",
    "subtype",
    "score",
}

COMPACT_ANNOTATION_METADATA_KEYS = {
    "concept_uri",
    "match_source",
    "matched_value",
    "wikidata",
    "normalized",
    "grain",
    "unit",
    "multiplier",
    "multiplier_value",
    "duckling_dim",
}

COMPACT_RELATION_KEYS = {
    "id",
    "type",
    "predicate",
    "arguments",
    "source",
    "score",
}

COMPACT_RELATION_PREDICATE_KEYS = {
    "start",
    "end",
    "text",
    "lemma",
}

COMPACT_RELATION_ARGUMENT_KEYS = {
    "role",
    "start",
    "end",
    "text",
    "annotation_id",
}

def apply_output_profile(
    data: dict[str, Any],
    *,
    profile: str = "compact",
) -> dict[str, Any]:
    if profile == "full":
        return deepcopy(data)

    if profile == "compact":
        return compact_corpus(data)

    raise ValueError(f"Unsupported output profile: {profile}")


def compact_corpus(data: dict[str, Any]) -> dict[str, Any]:
    documents = [
        compact_document(document)
        for document in data.get("documents", [])
    ]

    metadata = compact_corpus_metadata(
        data.get("metadata", {}),
    )

    result: dict[str, Any] = {
        "documents": documents,
    }

    if metadata:
        result["metadata"] = metadata

    return result


def compact_corpus_metadata(
    metadata: dict[str, Any],
) -> dict[str, Any]:
    compact: dict[str, Any] = {}

    if "layer_colors" in metadata:
        compact["layer_colors"] = metadata["layer_colors"]

    return compact


def compact_document(
    document: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "text": document.get("text", ""),
        "annotations": [
            compact_annotation(annotation)
            for annotation in document.get("annotations", [])
        ],
        "relations": [
            compact_relation(relation)
            for relation in document.get("relations", [])
        ],
    }

    metadata = compact_document_metadata(
        document.get("metadata", {}),
    )

    if metadata:
        result["metadata"] = metadata

    return result


def compact_document_metadata(
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: value
        for key, value in metadata.items()
        if key in COMPACT_DOCUMENT_METADATA_KEYS
    }


def compact_annotation(
    annotation: dict[str, Any],
) -> dict[str, Any]:
    result = {
        key: value
        for key, value in annotation.items()
        if key in COMPACT_ANNOTATION_KEYS
        and value is not None
    }

    metadata = compact_annotation_metadata(
        annotation.get("metadata", {}),
    )

    if metadata:
        result["metadata"] = metadata

    return result


def compact_annotation_metadata(
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: value
        for key, value in metadata.items()
        if key in COMPACT_ANNOTATION_METADATA_KEYS
        and value is not None
    }

def compact_relation(
    relation: dict[str, Any],
) -> dict[str, Any]:
    result = {
        key: value
        for key, value in relation.items()
        if key in COMPACT_RELATION_KEYS
        and value is not None
    }

    predicate = relation.get("predicate")

    if predicate is not None:
        result["predicate"] = compact_relation_predicate(
            predicate
        )

    result["arguments"] = [
        compact_relation_argument(argument)
        for argument in relation.get("arguments", [])
    ]

    return result


def compact_relation_predicate(
    predicate: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: value
        for key, value in predicate.items()
        if key in COMPACT_RELATION_PREDICATE_KEYS
        and value is not None
    }


def compact_relation_argument(
    argument: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: value
        for key, value in argument.items()
        if key in COMPACT_RELATION_ARGUMENT_KEYS
        and value is not None
    }