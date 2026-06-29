from typing import Any


LAYER_PRIORITY = {
    "contact": 100,
    "social": 90,
    "entity": 80,
    "temporal": 70,
    "cantidades": 70,
    "quantity": 70,
    "pattern": 60,
    "ontology": 10,
}


def select_visible_annotations(
    annotations: list[Any],
) -> list[Any]:
    """
    Select non-overlapping annotations for visual rendering.

    This does not modify the original annotations. It only chooses which
    annotations should be painted in renderers.

    Higher-priority layers, metadata priority and longer spans are preferred.
    """
    selected: list[Any] = []

    sorted_annotations = sorted(
        annotations,
        key=_render_priority,
        reverse=True,
    )

    for annotation in sorted_annotations:
        if not _overlaps_any(annotation, selected):
            selected.append(annotation)

    return sorted(
        selected,
        key=lambda ann: (_get(ann, "start"), _get(ann, "end")),
    )


def _render_priority(annotation: Any) -> tuple[int, int, int]:
    layer = _get(annotation, "layer")
    start = _get(annotation, "start")
    end = _get(annotation, "end")
    metadata = _get(annotation, "metadata", {}) or {}

    layer_priority = LAYER_PRIORITY.get(layer, 0)
    metadata_priority = int(metadata.get("priority", 0) or 0)
    length = end - start

    return (
        layer_priority,
        metadata_priority,
        length,
    )


def _overlaps_any(annotation: Any, selected: list[Any]) -> bool:
    return any(
        _overlaps(
            _get(annotation, "start"),
            _get(annotation, "end"),
            _get(existing, "start"),
            _get(existing, "end"),
        )
        for existing in selected
    )


def _overlaps(
    start_a: int,
    end_a: int,
    start_b: int,
    end_b: int,
) -> bool:
    return start_a < end_b and start_b < end_a


def _get(annotation: Any, key: str, default: Any = None) -> Any:
    if isinstance(annotation, dict):
        return annotation.get(key, default)

    return getattr(annotation, key, default)