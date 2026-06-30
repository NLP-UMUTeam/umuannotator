from __future__ import annotations

from typing import Callable

from umuannotator.document.model import Annotation


def overlaps(
    first: Annotation,
    second: Annotation,
) -> bool:
    return first.start < second.end and second.start < first.end


def select_non_overlapping(
    annotations: list[Annotation],
    *,
    priority: Callable[[Annotation], tuple] | None = None,
) -> list[Annotation]:
    if priority is None:
        priority = default_priority

    selected: list[Annotation] = []

    candidates = sorted(
        annotations,
        key=priority,
        reverse=True,
    )

    for annotation in candidates:
        if not any(overlaps(annotation, existing) for existing in selected):
            selected.append(annotation)

    return sorted(
        selected,
        key=lambda annotation: (annotation.start, annotation.end),
    )


def default_priority(annotation: Annotation) -> tuple[int, int]:
    return (
        annotation.end - annotation.start,
        annotation.start,
    )


def resolve_layer_overlaps(
    annotations: list[Annotation],
    *,
    layer: str,
    priority: Callable[[Annotation], tuple] | None = None,
) -> list[Annotation]:
    target = [
        annotation
        for annotation in annotations
        if annotation.layer == layer
    ]

    others = [
        annotation
        for annotation in annotations
        if annotation.layer != layer
    ]

    selected = select_non_overlapping(
        target,
        priority=priority,
    )

    return sorted(
        others + selected,
        key=lambda annotation: (annotation.start, annotation.end),
    )