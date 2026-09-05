from __future__ import annotations

from typing import Any

from umuannotator.document import Document


def find_dependent(
    words: list[dict[str, Any]],
    *,
    head: int,
    deprel: str,
) -> dict[str, Any] | None:
    for word in words:
        if (
            word.get("head") == head
            and word.get("deprel") == deprel
        ):
            return word

    return None


def find_dependents(
    words: list[dict[str, Any]],
    *,
    head: int,
    deprel: str,
) -> list[dict[str, Any]]:
    return [
        word
        for word in words
        if (
            word.get("head") == head
            and word.get("deprel") == deprel
        )
    ]


def build_children_index(
    words: list[dict[str, Any]],
) -> dict[int, list[int]]:
    children_by_head: dict[int, list[int]] = {}

    for word in words:
        head = word.get("head")

        if head is None:
            continue

        children_by_head.setdefault(
            head,
            [],
        ).append(word["id"])

    return children_by_head


def collect_subtree_ids(
    word_id: int,
    children_by_head: dict[int, list[int]],
) -> set[int]:
    result = {word_id}

    for child_id in children_by_head.get(
        word_id,
        [],
    ):
        result.update(
            collect_subtree_ids(
                child_id,
                children_by_head,
            )
        )

    return result


def dependency_subtree_span(
    *,
    document: Document,
    word: dict[str, Any],
    words_by_id: dict[int, dict[str, Any]],
    children_by_head: dict[int, list[int]],
) -> dict[str, Any]:
    subtree_ids = collect_subtree_ids(
        word["id"],
        children_by_head,
    )

    subtree_words = [
        words_by_id[word_id]
        for word_id in subtree_ids
        if word_id in words_by_id
    ]

    subtree_words = [
        item
        for item in subtree_words
        if (
            item.get("start") is not None
            and item.get("end") is not None
        )
    ]

    if not subtree_words:
        return {
            "start": word["start"],
            "end": word["end"],
            "text": document.text[
                word["start"]:
                word["end"]
            ],
        }

    start = min(
        item["start"]
        for item in subtree_words
    )

    end = max(
        item["end"]
        for item in subtree_words
    )

    return {
        "start": start,
        "end": end,
        "text": document.text[start:end],
    }


def get_polarity(
    words: list[dict[str, Any]],
    *,
    predicate_id: int,
) -> str:
    for word in words:
        if word.get("head") != predicate_id:
            continue

        feats = word.get("feats") or ""

        if "Polarity=Neg" in feats:
            return "negative"

        lemma = word.get("lemma")

        if (
            isinstance(lemma, str)
            and lemma.lower() == "no"
        ):
            return "negative"

    return "positive"


def find_inherited_subject(
    *,
    predicate_word: dict[str, Any],
    words: list[dict[str, Any]],
    words_by_id: dict[int, dict[str, Any]],
) -> tuple[
    dict[str, Any] | None,
    int | None,
    str | None,
]:
    deprel = predicate_word.get("deprel")

    if deprel not in {
        "conj",
        "advcl",
        "xcomp",
    }:
        return None, None, None

    parent_id = predicate_word.get("head")
    parent_word = words_by_id.get(parent_id)

    if (
        parent_word is None
        or parent_word.get("upos") != "VERB"
    ):
        return None, None, None

    if deprel == "advcl":
        feats = predicate_word.get("feats") or ""

        if "VerbForm=Fin" not in feats:
            return None, None, None

        has_mark = any(
            word.get("head") == predicate_word["id"]
            and word.get("deprel") == "mark"
            for word in words
        )

        if has_mark:
            return None, None, None

    subject = find_dependent(
        words,
        head=parent_id,
        deprel="nsubj",
    )

    if subject is None:
        return None, None, None

    if deprel == "conj":
        inheritance_type = "coordination"

    elif deprel == "advcl":
        inheritance_type = "asyndetic_coordination"

    else:
        inheritance_type = "xcomp_control"

    return (
        subject,
        parent_id,
        inheritance_type,
    )


def is_finite_predicate(
    word: dict[str, Any],
) -> bool:
    feats = word.get("feats") or ""

    return "VerbForm=Fin" in feats