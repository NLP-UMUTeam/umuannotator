from dataclasses import dataclass, field
from typing import Any


@dataclass
class Annotation:
    start: int
    end: int
    text: str
    label: str
    layer: str
    source: str | None = None
    type: str | None = None
    subtype: str | None = None
    score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict) 


@dataclass
class Document:
    text: str
    annotations: list[Annotation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_annotation(self, annotation: Annotation) -> None:
        self.annotations.append(annotation)

    def by_layer(self, layer: str) -> list[Annotation]:
        return [
            annotation
            for annotation in self.annotations
            if annotation.layer == layer
        ]

    def sorted_annotations(self) -> list[Annotation]:
        return sorted(
            self.annotations,
            key=lambda annotation: (
                annotation.start,
                -(annotation.end - annotation.start),
                annotation.layer,
            ),
        )