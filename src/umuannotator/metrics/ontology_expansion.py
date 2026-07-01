from __future__ import annotations

from collections import deque
from typing import Any

from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL


def rdf_to_expansion_graph(
    rdf_graph: Graph,
    *,
    include_subclass: bool = True,
    include_type: bool = True,
) -> dict[str, set[str]]:
    """
    Build an ontology expansion adjacency map using RDF URIs.

    The returned graph maps:

        source_uri -> related_uri

    For subclass relations:

        child -> parent

    For rdf:type relations:

        individual -> class
    """
    adjacency: dict[str, set[str]] = {}

    for subject in rdf_graph.subjects():
        adjacency.setdefault(str(subject), set())

    for obj in rdf_graph.objects():
        adjacency.setdefault(str(obj), set())

    if include_subclass:
        for child, parent in rdf_graph.subject_objects(RDFS.subClassOf):
            adjacency.setdefault(str(child), set()).add(str(parent))
            adjacency.setdefault(str(parent), set())

    if include_type:
        for individual, class_uri in rdf_graph.subject_objects(RDF.type):
            if class_uri in {OWL.Class, OWL.NamedIndividual}:
                continue

            adjacency.setdefault(str(individual), set()).add(str(class_uri))
            adjacency.setdefault(str(class_uri), set())

    return adjacency


def graph_to_distance_map(
    graph: Any,
    *,
    max_distance: int,
    direction: str = "outgoing",
) -> dict[str, dict[str, int]]:
    adjacency = _to_adjacency(
        graph,
        direction=direction,
    )

    return {
        source: _distances_from(
            source,
            adjacency=adjacency,
            max_distance=max_distance,
        )
        for source in adjacency
    }


def _to_adjacency(
    graph: Any,
    *,
    direction: str = "outgoing",
) -> dict[str, set[str]]:
    if direction not in {
        "outgoing",
        "incoming",
        "both",
    }:
        raise ValueError(
            f"Unsupported graph direction: {direction}"
        )

    if isinstance(graph, dict):
        return _dict_to_adjacency(
            graph,
            direction=direction,
        )

    if hasattr(graph, "nodes") and hasattr(graph, "edges"):
        return _networkx_to_adjacency(
            graph,
            direction=direction,
        )

    raise TypeError(
        f"Unsupported ontology graph type for TF-IDF-e: {type(graph)!r}"
    )


def _dict_to_adjacency(
    graph: dict,
    *,
    direction: str,
) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {}

    for source, targets in graph.items():
        source = str(source)
        adjacency.setdefault(source, set())

        if isinstance(targets, dict):
            iterable_targets = targets.keys()
        else:
            iterable_targets = targets

        for target in iterable_targets:
            target = str(target)

            adjacency.setdefault(source, set())
            adjacency.setdefault(target, set())

            if direction in {
                "outgoing",
                "both",
            }:
                adjacency[source].add(target)

            if direction in {
                "incoming",
                "both",
            }:
                adjacency[target].add(source)

    return adjacency


def _networkx_to_adjacency(
    graph: Any,
    *,
    direction: str,
) -> dict[str, set[str]]:
    adjacency = {
        str(node): set()
        for node in graph.nodes
    }

    for source, target in graph.edges():
        source = str(source)
        target = str(target)

        adjacency.setdefault(source, set())
        adjacency.setdefault(target, set())

        if direction in {
            "outgoing",
            "both",
        }:
            adjacency[source].add(target)

        if direction in {
            "incoming",
            "both",
        }:
            adjacency[target].add(source)

    return adjacency


def _distances_from(
    source: str,
    *,
    adjacency: dict[str, set[str]],
    max_distance: int,
) -> dict[str, int]:
    distances: dict[str, int] = {}
    queue = deque([(source, 0)])
    visited = {source}

    while queue:
        current, distance = queue.popleft()

        if distance >= max_distance:
            continue

        for neighbor in adjacency.get(current, set()):
            if neighbor in visited:
                continue

            next_distance = distance + 1
            visited.add(neighbor)
            distances[neighbor] = next_distance
            queue.append((neighbor, next_distance))

    return distances