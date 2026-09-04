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
class RelationPredicate:
    start: int
    end: int
    text: str
    lemma: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationArgument:
    role: str
    start: int
    end: int
    text: str
    annotation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Relation:
    type: str
    predicate: RelationPredicate
    arguments: list[RelationArgument] = field(default_factory=list)
    source: str | None = None
    score: float | None = None
    id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    text: str
    annotations: list[Annotation] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_annotation(self, annotation: Annotation) -> None:
        self.annotations.append(annotation)

    def add_relation(self, relation: Relation) -> None:
        self.relations.append(relation)