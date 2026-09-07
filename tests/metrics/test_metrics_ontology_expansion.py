from umuannotator.metrics.ontology_expansion import graph_to_distance_map
from umuannotator.metrics.ontology_expansion import rdf_to_expansion_graph
import pytest
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, OWL


def test_graph_to_distance_map_from_dict_of_lists():
    graph = {
        "Pizza": ["Food"],
        "Food": ["Product"],
        "Product": [],
    }

    result = graph_to_distance_map(
        graph,
        max_distance=2,
    )

    assert result["Pizza"] == {
        "Food": 1,
        "Product": 2,
    }


def test_graph_to_distance_map_respects_max_distance():
    graph = {
        "Pizza": ["Food"],
        "Food": ["Product"],
        "Product": [],
    }

    result = graph_to_distance_map(
        graph,
        max_distance=1,
    )

    assert result["Pizza"] == {
        "Food": 1,
    }


def test_graph_to_distance_map_from_dict_of_dicts():
    graph = {
        "Pizza": {
            "Food": {
                "relation": "subClassOf",
            },
        },
        "Food": {},
    }

    result = graph_to_distance_map(
        graph,
        max_distance=1,
    )

    assert result["Pizza"] == {
        "Food": 1,
    }


def test_graph_to_distance_map_supports_incoming_direction():
    graph = {
        "Politics": ["NewsTopic"],
        "NewsTopic": [],
    }

    result = graph_to_distance_map(
        graph,
        max_distance=1,
        direction="incoming",
    )

    assert result["NewsTopic"] == {
        "Politics": 1,
    }


def test_graph_to_distance_map_supports_both_direction():
    graph = {
        "Politics": ["NewsTopic"],
        "NewsTopic": [],
    }

    result = graph_to_distance_map(
        graph,
        max_distance=1,
        direction="both",
    )

    assert result["Politics"] == {
        "NewsTopic": 1,
    }
    assert result["NewsTopic"] == {
        "Politics": 1,
    }


def test_graph_to_distance_map_rejects_unknown_direction():
    graph = {
        "Politics": ["NewsTopic"],
    }

    try:
        graph_to_distance_map(
            graph,
            max_distance=1,
            direction="sideways",
        )
    except ValueError as error:
        assert "Unsupported graph direction" in str(error)
    else:
        raise AssertionError("Expected ValueError")
    

def test_graph_to_distance_map_outgoing_direction_by_default():
    graph = {
        "Politics": ["NewsTopic"],
        "NewsTopic": ["RootTopic"],
        "RootTopic": [],
    }

    result = graph_to_distance_map(
        graph,
        max_distance=2,
    )

    assert result["Politics"] == {
        "NewsTopic": 1,
        "RootTopic": 2,
    }


def test_graph_to_distance_map_incoming_direction():
    graph = {
        "Politics": ["NewsTopic"],
        "Sports": ["NewsTopic"],
        "NewsTopic": [],
    }

    result = graph_to_distance_map(
        graph,
        max_distance=1,
        direction="incoming",
    )

    assert result["NewsTopic"] == {
        "Politics": 1,
        "Sports": 1,
    }


def test_graph_to_distance_map_both_direction():
    graph = {
        "Politics": ["NewsTopic"],
        "NewsTopic": [],
    }

    result = graph_to_distance_map(
        graph,
        max_distance=1,
        direction="both",
    )

    assert result["Politics"] == {
        "NewsTopic": 1,
    }
    assert result["NewsTopic"] == {
        "Politics": 1,
    }


def test_graph_to_distance_map_rejects_unknown_direction():
    with pytest.raises(ValueError, match="Unsupported graph direction"):
        graph_to_distance_map(
            {
                "Politics": ["NewsTopic"],
            },
            max_distance=1,
            direction="sideways",
        )


def test_rdf_to_expansion_graph_adds_subclass_edges():
    ns = Namespace("http://example.org/test#")
    graph = Graph()

    graph.add((ns.Politics, RDF.type, OWL.Class))
    graph.add((ns.NewsTopic, RDF.type, OWL.Class))
    graph.add((ns.Politics, RDFS.subClassOf, ns.NewsTopic))

    result = rdf_to_expansion_graph(graph)

    assert result[str(ns.Politics)] == {
        str(ns.NewsTopic),
    }


def test_rdf_to_expansion_graph_adds_type_edges_for_individuals():
    ns = Namespace("http://example.org/test#")
    graph = Graph()

    graph.add((ns.DANA, RDF.type, OWL.NamedIndividual))
    graph.add((ns.DANA, RDF.type, ns.WeatherEvent))

    result = rdf_to_expansion_graph(graph)

    assert str(ns.WeatherEvent) in result[str(ns.DANA)]


def test_rdf_to_expansion_graph_skips_meta_type_edges():
    ns = Namespace("http://example.org/test#")
    graph = Graph()

    graph.add((ns.Politics, RDF.type, OWL.Class))

    result = rdf_to_expansion_graph(graph)

    assert str(OWL.Class) not in result[str(ns.Politics)]


def test_rdf_to_expansion_graph_can_disable_subclass_edges():
    ns = Namespace("http://example.org/test#")
    graph = Graph()

    graph.add((ns.Politics, RDFS.subClassOf, ns.NewsTopic))

    result = rdf_to_expansion_graph(
        graph,
        include_subclass=False,
    )

    assert str(ns.NewsTopic) not in result[str(ns.Politics)]


def test_rdf_to_expansion_graph_can_disable_type_edges():
    ns = Namespace("http://example.org/test#")
    graph = Graph()

    graph.add((ns.DANA, RDF.type, ns.WeatherEvent))

    result = rdf_to_expansion_graph(
        graph,
        include_type=False,
    )

    assert str(ns.WeatherEvent) not in result[str(ns.DANA)]