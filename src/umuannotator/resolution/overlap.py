from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar
from typing import Any

from umuannotator.document.model import Annotation


T = TypeVar("T", bound=Annotation)


def overlaps(
    first: Annotation,
    second: Annotation,
) -> bool:
    return spans_overlap(
        first.start,
        first.end,
        second.start,
        second.end,
    )


def span_length(
    annotation: Annotation,
) -> int:
    return annotation.end - annotation.start


def select_non_overlapping(
    annotations: list[T],
    *,
    priority: Callable[[T], tuple] | None = None,
) -> list[T]:
    """
    Select a non-overlapping subset of annotations.

    By default, longer spans win. Ties keep original order.
    The returned annotations are sorted by text position.
    """
    indexed_annotations = list(enumerate(annotations))

    candidates = sorted(
        indexed_annotations,
        key=lambda item: _priority_key(
            item,
            priority=priority,
        ),
    )

    selected: list[tuple[int, T]] = []

    for index, annotation in candidates:
        if not any(
            overlaps(annotation, selected_annotation)
            for _, selected_annotation in selected
        ):
            selected.append((index, annotation))

    return [
        annotation
        for _, annotation in sorted(
            selected,
            key=lambda item: (
                item[1].start,
                item[1].end,
                item[0],
            ),
        )
    ]


def resolve_layer_overlaps(
    annotations: list[T],
    *,
    layer: str,
    priority: Callable[[T], tuple] | None = None,
) -> list[T]:
    target_annotations = [
        annotation
        for annotation in annotations
        if annotation.layer == layer
    ]

    other_annotations = [
        annotation
        for annotation in annotations
        if annotation.layer != layer
    ]

    selected = select_non_overlapping(
        target_annotations,
        priority=priority,
    )

    return sorted(
        other_annotations + selected,
        key=lambda annotation: (
            annotation.start,
            annotation.end,
        ),
    )


def _priority_key(
    item: tuple[int, T],
    *,
    priority: Callable[[T], tuple] | None,
) -> tuple:
    index, annotation = item

    if priority is not None:
        custom_priority = priority(annotation)

        return (
            *tuple(-value for value in custom_priority),
            index,
        )

    return (
        -span_length(annotation),
        index,
    )


def spans_overlap(
    start_a: int,
    end_a: int,
    start_b: int,
    end_b: int,
) -> bool:
    return start_a < end_b and start_b < end_a


def annotation_overlaps(
    first: Any,
    second: Any,
) -> bool:
    return spans_overlap(
        _get(first, "start"),
        _get(first, "end"),
        _get(second, "start"),
        _get(second, "end"),
    )


def _get(
    annotation: Any,
    key: str,
    default: Any = None,
) -> Any:
    if isinstance(annotation, dict):
        return annotation.get(key, default)

    return getattr(annotation, key, default)