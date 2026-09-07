import pytest

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



def test_extended_salience_observed_concept_has_observed_score():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "política",
                        "label": "Politics",
                        "layer": "ontology",
                        "metadata": {
                            "concept_uri": "http://example.org/news-es#Politics",
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

    items = {
        item["concept_uri"]: item
        for item in result["items"]
    }

    politics = items["http://example.org/news-es#Politics"]

    assert politics["tf"] == 1
    assert politics["df"] == 1
    assert politics["idf"] > 0
    assert politics["observed_score"] > 0
    assert politics["expanded_score"] == 0
    assert politics["score"] == politics["observed_score"]


def test_extended_salience_propagates_to_parent_concept():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "política",
                        "label": "Politics",
                        "layer": "ontology",
                        "metadata": {
                            "concept_uri": "http://example.org/news-es#Politics",
                        },
                    }
                ]
            }
        ]
    }

    result = compute_extended_salience(
        data,
        ontology_graph={
            "http://example.org/news-es#Politics": {
                "http://example.org/news-es#NewsTopic": 1,
            },
        },
        top=10,
        decay=0.5,
    )

    items = {
        item["concept_uri"]: item
        for item in result["items"]
    }

    politics = items["http://example.org/news-es#Politics"]
    news_topic = items["http://example.org/news-es#NewsTopic"]

    assert politics["observed_score"] > 0
    assert politics["expanded_score"] == 0

    assert news_topic["tf"] == 0
    assert news_topic["df"] == 0
    assert news_topic["observed_score"] == 0
    assert news_topic["expanded_score"] == pytest.approx(
        politics["observed_score"] * 0.5,
    )
    assert news_topic["score"] == news_topic["expanded_score"]


def test_extended_salience_respects_decay_by_distance():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "política",
                        "label": "Politics",
                        "layer": "ontology",
                        "metadata": {
                            "concept_uri": "Politics",
                        },
                    }
                ]
            }
        ]
    }

    result = compute_extended_salience(
        data,
        ontology_graph={
            "Politics": {
                "NewsTopic": 1,
                "RootTopic": 2,
            },
        },
        top=10,
        decay=0.5,
    )

    items = {
        item["concept_uri"]: item
        for item in result["items"]
    }

    observed_score = items["Politics"]["observed_score"]

    assert items["NewsTopic"]["expanded_score"] == pytest.approx(
        observed_score * 0.5,
    )
    assert items["RootTopic"]["expanded_score"] == pytest.approx(
        observed_score * 0.25,
    )


def test_extended_salience_respects_max_distance():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "política",
                        "label": "Politics",
                        "layer": "ontology",
                        "metadata": {
                            "concept_uri": "Politics",
                        },
                    }
                ]
            }
        ]
    }

    result = compute_extended_salience(
        data,
        ontology_graph={
            "Politics": {
                "NewsTopic": 1,
                "RootTopic": 2,
            },
        },
        top=10,
        max_distance=1,
    )

    concepts = {
        item["concept_uri"]
        for item in result["items"]
    }

    assert "Politics" in concepts
    assert "NewsTopic" in concepts
    assert "RootTopic" not in concepts


def test_extended_salience_metadata_includes_method_parameters():
    result = compute_extended_salience(
        {
            "documents": [],
        },
        ontology_graph={},
        top=10,
        layer="ontology",
        max_distance=3,
        decay=0.25,
        direction="both",
    )

    assert result["method"] == "tfidf-e"
    assert result["layer"] == "ontology"
    assert result["max_distance"] == 3
    assert result["decay"] == 0.25
    assert result["direction"] == "both"


def test_extended_salience_records_expanded_from_contributions():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "política",
                        "label": "Politics",
                        "layer": "ontology",
                        "metadata": {
                            "concept_uri": "Politics",
                        },
                    }
                ]
            }
        ]
    }

    result = compute_extended_salience(
        data,
        ontology_graph={
            "Politics": {
                "NewsTopic": 1,
            },
        },
        top=10,
        decay=0.5,
    )

    items = {
        item["concept_uri"]: item
        for item in result["items"]
    }

    expanded_from = items["NewsTopic"]["expanded_from"]

    assert expanded_from == [
        {
            "source": "Politics",
            "distance": 1,
            "contribution": pytest.approx(
                items["Politics"]["observed_score"] * 0.5,
            ),
        }
    ]


def test_extended_salience_ignores_annotations_without_concept_uri():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "política",
                        "label": "Politics",
                        "layer": "ontology",
                        "metadata": {},
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


def test_extended_salience_filters_by_layer():
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
                    },
                    {
                        "text": "política",
                        "label": "Politics",
                        "layer": "ontology",
                        "metadata": {
                            "concept_uri": "Politics",
                        },
                    },
                ]
            }
        ]
    }

    result = compute_extended_salience(
        data,
        ontology_graph={},
        layer="entity",
        top=10,
    )

    concepts = [
        item["concept_uri"]
        for item in result["items"]
    ]

    assert concepts == [
        "CountrySpain",
    ]