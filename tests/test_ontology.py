from umuannotator.ontology.loader import load_ontology
from umuannotator.ontology.index import build_index
from umuannotator.ontology.graph import build_graph, distances_from


def test_load_pizza_ontology():
    graph = load_ontology("resources/pizza.owl")

    assert len(graph) > 0


def test_build_pizza_index(): 
    graph = load_ontology("resources/pizza.owl")
    concepts = build_index(graph)

    assert "Pizza" in concepts
    assert "HawaiianPizza" in concepts
    assert "pizza hawaiana" in concepts["HawaiianPizza"].labels
    assert "hawaiana" in concepts["HawaiianPizza"].aliases


def test_pizza_graph_distances():
    graph = load_ontology("resources/pizza.owl")
    concepts = build_index(graph)
    ontology_graph = build_graph(concepts)

    distances = distances_from(
        ontology_graph,
        "HawaiianPizza",
        max_distance=3,
    )

    assert distances["HawaiianPizza"] == 0
    assert distances["Pizza"] == 1
    assert distances["Food"] == 2