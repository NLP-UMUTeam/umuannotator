import networkx as nx

from umuannotator.ontology.model import Concept


def build_graph(concepts: dict[str, Concept]) -> nx.Graph:
    graph = nx.Graph()

    for name, concept in concepts.items():
        graph.add_node(name)

        for parent in concept.parents:
            graph.add_edge(name, parent, weight=1)

    return graph


def distances_from(graph: nx.Graph, concept_name: str, max_distance: int | None = None):
    distances = nx.single_source_dijkstra_path_length(
        graph,
        concept_name,
        cutoff=max_distance,
        weight="weight",
    )

    return dict(distances)