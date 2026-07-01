from umuannotator.metrics.extended_salience import compute_extended_salience


def test_extended_salience_includes_observed_concept_score():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "Pizza",
                        "label": "Pizza",
                        "layer": "ontology",
                        "metadata": {
                            "concept_uri": "Pizza",
                        },
                    }
                ]
            }
        ]
    }

    result = compute_extended_salience(
        data,
        ontology_graph={},
        top=10,
    )

    assert result["method"] == "tfidf-e"
    assert result["items"][0]["concept_uri"] == "Pizza"
    assert result["items"][0]["tf"] == 1
    assert result["items"][0]["df"] == 1
    assert result["items"][0]["observed_score"] > 0
    assert result["items"][0]["expanded_score"] == 0


def test_extended_salience_expands_score_to_related_concepts():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "Pizza",
                        "label": "Pizza",
                        "layer": "ontology",
                        "metadata": {
                            "concept_uri": "Pizza",
                        },
                    }
                ]
            }
        ]
    }

    result = compute_extended_salience(
        data,
        ontology_graph={
            "Pizza": {
                "Food": 1,
            },
        },
        top=10,
        decay=0.5,
    )

    items = {
        item["concept_uri"]: item
        for item in result["items"]
    }

    assert "Pizza" in items
    assert "Food" in items

    assert items["Food"]["observed_score"] == 0
    assert items["Food"]["expanded_score"] == (
        items["Pizza"]["observed_score"] * 0.5
    )


def test_extended_salience_respects_max_distance():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "Pizza",
                        "label": "Pizza",
                        "layer": "ontology",
                        "metadata": {
                            "concept_uri": "Pizza",
                        },
                    }
                ]
            }
        ]
    }

    result = compute_extended_salience(
        data,
        ontology_graph={
            "Pizza": {
                "Food": 1,
                "Product": 2,
            },
        },
        top=10,
        max_distance=1,
    )

    concepts = {
        item["concept_uri"]
        for item in result["items"]
    }

    assert "Pizza" in concepts
    assert "Food" in concepts
    assert "Product" not in concepts


def test_extended_salience_ignores_non_ontology_annotations():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "hoy",
                        "label": "DATE",
                        "layer": "temporal",
                        "metadata": {
                            "normalized": "2026-07-01",
                        },
                    }
                ]
            }
        ]
    }

    result = compute_extended_salience(
        data,
        ontology_graph={},
        top=10,
    )

    assert result["items"] == []


def test_extended_salience_uses_requested_layer():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "España",
                        "label": "COUNTRY",
                        "layer": "entity",
                        "metadata": {
                            "concept_uri": "CountrySpain",
                        },
                    }
                ]
            }
        ]
    }

    result = compute_extended_salience(
        data,
        ontology_graph={},
        top=10,
        layer="entity",
    )

    assert result["items"][0]["concept_uri"] == "CountrySpain"


def test_extended_salience_includes_direction():
    data = {
        "documents": [],
    }

    result = compute_extended_salience(
        data,
        ontology_graph={},
        direction="both",
    )

    assert result["direction"] == "both"