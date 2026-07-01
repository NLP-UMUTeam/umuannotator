import pytest

from umuannotator.document.model import Annotation
from umuannotator.resolution.resolver import (
    ResolverConfig,
    apply_resolver_if_enabled,
    resolver_config_from_dict,
    resolve_annotations,
    resolve_longest_non_overlapping,
)


def ann(
    start: int,
    end: int,
    text: str,
    *,
    layer: str = "test",
    label: str = "TEST",
) -> Annotation:
    return Annotation(
        start=start,
        end=end,
        text=text,
        label=label,
        layer=layer,
        source="test",
        type="test",
    )


def test_longest_span_wins_when_annotations_overlap():
    annotations = [
        ann(0, 2, "22"),
        ann(0, 13, "22 millones"),
    ]

    resolved = resolve_longest_non_overlapping(annotations)

    assert resolved == [
        annotations[1],
    ]


def test_non_overlapping_annotations_are_kept():
    annotations = [
        ann(0, 5, "Pedro"),
        ann(12, 17, "Madrid"),
    ]

    resolved = resolve_longest_non_overlapping(annotations)

    assert resolved == annotations


def test_tie_keeps_original_order_winner():
    annotations = [
        ann(0, 5, "Pedro", layer="ner"),
        ann(0, 5, "Pedro", layer="ontology"),
    ]

    resolved = resolve_longest_non_overlapping(annotations)

    assert resolved == [
        annotations[0],
    ]


def test_selected_annotations_are_returned_in_text_order():
    annotations = [
        ann(20, 25, "Pasta"),
        ann(0, 5, "Pizza"),
        ann(10, 23, "larga larga"),
    ]

    resolved = resolve_longest_non_overlapping(annotations)

    assert resolved == [
        annotations[1],
        annotations[2],
    ]


def test_touching_annotations_do_not_overlap():
    annotations = [
        ann(0, 5, "Pedro"),
        ann(5, 12, "Sánchez"),
    ]

    resolved = resolve_longest_non_overlapping(annotations)

    assert resolved == annotations


def test_resolve_annotations_rejects_unknown_strategy():
    with pytest.raises(ValueError, match="Unsupported resolver strategy"):
        resolve_annotations(
            [],
            strategy="unknown",
        )


def test_resolver_config_defaults_to_disabled():
    config = resolver_config_from_dict(None)

    assert config == ResolverConfig(
        enabled=False,
        strategy="longest_non_overlapping",
    )


def test_resolver_config_from_dict():
    config = resolver_config_from_dict(
        {
            "enabled": True,
            "strategy": "longest_non_overlapping",
        }
    )

    assert config == ResolverConfig(
        enabled=True,
        strategy="longest_non_overlapping",
    )


def test_apply_resolver_if_disabled_returns_original_annotations():
    annotations = [
        ann(0, 5, "Pedro"),
        ann(0, 10, "Pedro test"),
    ]

    resolved = apply_resolver_if_enabled(
        annotations,
        config=ResolverConfig(enabled=False),
    )

    assert resolved is annotations


def test_apply_resolver_if_enabled_resolves_annotations():
    annotations = [
        ann(0, 5, "Pedro"),
        ann(0, 10, "Pedro test"),
    ]

    resolved = apply_resolver_if_enabled(
        annotations,
        config=ResolverConfig(enabled=True),
    )

    assert resolved == [
        annotations[1],
    ]