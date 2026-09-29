from __future__ import annotations

from typing import Any

from umuannotator.annotation_enrichers.overlap import (
    AnnotationOverlapEnricher,
)

from umuannotator.annotation_enrichers.age import AgeEnricher


def build_annotation_enricher(
    config: dict[str, Any],
):
    name = config.get("name")

    if name == "overlap":
        return AnnotationOverlapEnricher(
            strategy=config.get(
                "strategy",
                "longest_non_overlapping",
            ),
            layer=config.get("layer"),
        )

    if name == "age":
        return AgeEnricher(
            temporal_layer=config.get(
                "temporal_layer",
                "temporal",
            ),
            lexical_semantics_layer=config.get(
                "lexical_semantics_layer",
                "lexical_semantics",
            ),
        )

    raise ValueError(
        f"Unknown annotation enricher: {name}"
    )


def build_annotation_enrichers(
    configs: list[dict[str, Any]] | None,
) -> list:
    if not configs:
        return []

    return [
        build_annotation_enricher(config)
        for config in configs
    ]