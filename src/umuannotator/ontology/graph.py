import networkx as nx


def build_graph(concepts, directed: bool = False):
    graph = nx.DiGraph() if directed else nx.Graph()

    for name, concept in concepts.items():
        graph.add_node(name)

        for parent in concept.parents:
            if parent:
                graph.add_edge(name, parent, weight=1)

    return graph


def distances_from(graph, concept_name: str, max_distance: int | None = None):
    return dict(
        nx.single_source_dijkstra_path_length(
            graph,
            concept_name,
            cutoff=max_distance,
            weight="weight",
        )
    )