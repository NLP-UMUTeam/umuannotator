from __future__ import annotations

from typing import Any

from umuannotator.document import (
    Document,
    RelationArgument,
    RelationPredicate,
)

from .syntax import dependency_subtree_span


def build_predicate(
    *,
    document: Document,
    predicate_word: dict[str, Any],
) -> RelationPredicate:
    return RelationPredicate(
        start=predicate_word["start"],
        end=predicate_word["end"],
        text=document.text[
            predicate_word["start"]:
            predicate_word["end"]
        ],
        lemma=predicate_word.get("lemma"),
        metadata={
            "word_id": predicate_word["id"],
        },
    )


def build_argument(
    *,
    document: Document,
    word: dict[str, Any],
    role: str,
    words_by_id: dict[int, dict[str, Any]],
    children_by_head: dict[int, list[int]],
) -> RelationArgument:
    span = dependency_subtree_span(
        document=document,
        word=word,
        words_by_id=words_by_id,
        children_by_head=children_by_head,
    )

    return RelationArgument(
        role=role,
        start=span["start"],
        end=span["end"],
        text=span["text"],
        metadata={
            "head_word_id": word["id"],
            "deprel": word.get("deprel"),
        },
    )