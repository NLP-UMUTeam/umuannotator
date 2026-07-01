from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from umuannotator.document.model import Annotation
from umuannotator.resolution.overlap import select_non_overlapping


@dataclass(frozen=True)
class ResolverConfig:
    enabled: bool = False
    strategy: str = "longest_non_overlapping"


def resolve_annotations(
    annotations: list[Annotation],
    *,
    strategy: str = "longest_non_overlapping",
) -> list[Annotation]:
    if strategy == "longest_non_overlapping":
        return resolve_longest_non_overlapping(annotations)

    raise ValueError(f"Unsupported resolver strategy: {strategy}")


def resolve_longest_non_overlapping(
    annotations: list[Annotation],
) -> list[Annotation]:
    return select_non_overlapping(annotations)


def resolver_config_from_dict(
    data: dict[str, Any] | None,
) -> ResolverConfig:
    if not data:
        return ResolverConfig()

    return ResolverConfig(
        enabled=bool(data.get("enabled", False)),
        strategy=str(
            data.get(
                "strategy",
                "longest_non_overlapping",
            )
        ),
    )


def apply_resolver_if_enabled(
    annotations: list[Annotation],
    *,
    config: ResolverConfig,
) -> list[Annotation]:
    if not config.enabled:
        return annotations

    return resolve_annotations(
        annotations,
        strategy=config.strategy,
    )