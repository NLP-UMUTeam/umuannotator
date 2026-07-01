from umuannotator.metrics.ontology_expansion import graph_to_distance_map


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