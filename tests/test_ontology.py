from umuannotator.ontology.graph import build_graph, distances_from
from umuannotator.ontology.index import build_index
from umuannotator.ontology.loader import load_ontology


CONFIG = {
    "ontology": {
        "relations": [
            {
                "property": "rdfs:subClassOf",
                "distance": 1,
                "direction": "child_to_parent",
            }
        ]
    }
}


def test_load_pizza_ontology():
    graph = load_ontology("resources/pizza.owl")

    assert len(graph) > 0


def test_build_pizza_index():
    graph = load_ontology("resources/pizza.owl")
    concepts = build_index(graph)

    pizza_uri = "http://example.org/pizza#Pizza"
    hawaiian_uri = "http://example.org/pizza#HawaiianPizza"

    assert pizza_uri in concepts
    assert hawaiian_uri in concepts
    assert concepts[hawaiian_uri].name == "HawaiianPizza"
    assert "pizza hawaiana" in concepts[hawaiian_uri].labels
    assert "hawaiana" in concepts[hawaiian_uri].aliases


def test_pizza_graph_distances():
    graph = load_ontology("resources/pizza.owl")
    ontology_graph = build_graph(graph, CONFIG)

    hawaiian_uri = "http://example.org/pizza#HawaiianPizza"
    pizza_uri = "http://example.org/pizza#Pizza"
    food_uri = "http://example.org/pizza#Food"

    distances = distances_from(
        ontology_graph,
        hawaiian_uri,
        max_distance=3,
    )

    assert distances[hawaiian_uri] == 0
    assert distances[pizza_uri] == 1
    assert distances[food_uri] == 2