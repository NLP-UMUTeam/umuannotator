from __future__ import annotations

from umuannotator.document import Document
from umuannotator.resolution.overlap import (
    resolve_layer_overlaps,
    select_non_overlapping,
)


class AnnotationOverlapEnricher:
    def __init__(
        self,
        *,
        strategy: str = "longest_non_overlapping",
        layer: str | None = None,
    ):
        self.strategy = strategy
        self.layer = layer

    def enrich(
        self,
        document: Document,
    ) -> Document:
        if self.strategy != "longest_non_overlapping":
            raise ValueError(
                "Unsupported annotation overlap strategy: "
                f"{self.strategy}"
            )

        if self.layer is None:
            document.annotations = select_non_overlapping(
                document.annotations
            )
        else:
            document.annotations = resolve_layer_overlaps(
                document.annotations,
                layer=self.layer,
            )

        return document