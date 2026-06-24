from dataclasses import dataclass, field
from typing import Any


@dataclass
class Concept:
    """
    Ontological concept extracted from an RDF/OWL graph.

    A concept can represent either an ``owl:Class`` or an
    ``owl:NamedIndividual`` depending on the ontology configuration.

    Design notes
    ------------
    ``uri`` is the stable internal identifier and should be used for
    graph nodes, semantic propagation and cross-component references.

    ``name`` is a human-readable short identifier derived from the URI.
    It is useful for display, labels and debugging, but it should not be
    treated as globally unique.

    ``metadata`` stores ontology-specific annotation properties such as
    code, category, priority or regex.
    """

    uri: str
    name: str

    labels: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)

    parent_uris: list[str] = field(default_factory=list)
    parents: list[str] = field(default_factory=list)

    entity_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)