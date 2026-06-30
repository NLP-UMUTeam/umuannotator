from umuannotator.annotators.overlap import (
    overlaps,
    resolve_layer_overlaps,
    select_non_overlapping,
)
from umuannotator.document import Annotation


def make_annotation(
    *,
    start: int,
    end: int,
    layer: str = "cantidades",
    text: str | None = None,
    label: str = "LABEL",
    source: str = "test",
    metadata: dict | None = None,
) -> Annotation:
    return Annotation(
        start=start,
        end=end,
        text=text or f"{start}:{end}",
        label=label,
        layer=layer,
        source=source,
        type="test",
        metadata=metadata or {},
    )


def annotation_spans(annotations):
    return [
        (annotation.start, annotation.end, annotation.layer)
        for annotation in annotations
    ]


def test_overlaps_returns_true_for_intersecting_spans():
    first = make_annotation(start=0, end=10)
    second = make_annotation(start=5, end=15)

    assert overlaps(first, second)


def test_overlaps_returns_false_for_adjacent_spans():
    first = make_annotation(start=0, end=10)
    second = make_annotation(start=10, end=20)

    assert not overlaps(first, second)


def test_overlaps_returns_false_for_disjoint_spans():
    first = make_annotation(start=0, end=10)
    second = make_annotation(start=20, end=30)

    assert not overlaps(first, second)


def test_select_non_overlapping_prefers_longer_span_by_default():
    short = make_annotation(start=0, end=6, text="22.000")
    long = make_annotation(start=0, end=15, text="22.000 millones")
    nested = make_annotation(start=7, end=15, text="millones")

    selected = select_non_overlapping(
        [short, long, nested],
    )

    assert [annotation.text for annotation in selected] == [
        "22.000 millones",
    ]


def test_select_non_overlapping_keeps_non_overlapping_annotations():
    first = make_annotation(start=0, end=5)
    second = make_annotation(start=10, end=20)

    selected = select_non_overlapping(
        [second, first],
    )

    assert annotation_spans(selected) == [
        (0, 5, "cantidades"),
        (10, 20, "cantidades"),
    ]


def test_select_non_overlapping_accepts_custom_priority():
    low_priority_long = make_annotation(
        start=0,
        end=20,
        metadata={"priority": 1},
    )
    high_priority_short = make_annotation(
        start=0,
        end=5,
        metadata={"priority": 10},
    )

    selected = select_non_overlapping(
        [low_priority_long, high_priority_short],
        priority=lambda annotation: (
            annotation.metadata.get("priority", 0),
            annotation.end - annotation.start,
        ),
    )

    assert selected == [high_priority_short]


def test_resolve_layer_overlaps_only_resolves_target_layer():
    quantity_long = make_annotation(
        start=0,
        end=15,
        layer="cantidades",
        text="22.000 millones",
    )
    quantity_nested = make_annotation(
        start=7,
        end=15,
        layer="cantidades",
        text="millones",
    )
    ontology_nested = make_annotation(
        start=7,
        end=15,
        layer="ontology",
        text="millones",
    )

    resolved = resolve_layer_overlaps(
        [quantity_nested, ontology_nested, quantity_long],
        layer="cantidades",
    )

    assert annotation_spans(resolved) == [
        (0, 15, "cantidades"),
        (7, 15, "ontology"),
    ]


def test_resolve_layer_overlaps_sorts_result_by_position():
    later = make_annotation(start=20, end=25, layer="cantidades")
    earlier = make_annotation(start=0, end=5, layer="ontology")

    resolved = resolve_layer_overlaps(
        [later, earlier],
        layer="cantidades",
    )

    assert annotation_spans(resolved) == [
        (0, 5, "ontology"),
        (20, 25, "cantidades"),
    ]