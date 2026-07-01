import pytest

from umuannotator.cli.metrics import (
    explain_salience_item,
    find_salience_item,
)


def sample_salience_data():
    return {
        "documents": 10,
        "method": "tfidf-e",
        "layer": "ontology",
        "max_distance": 2,
        "decay": 0.5,
        "direction": "both",
        "items": [
            {
                "concept_uri": "http://example.org/news-es#TrafficAccident",
                "canonical": "concept_uri:http://example.org/news-es#TrafficAccident",
                "display": "carretera",
                "label": "TrafficAccident",
                "score": 100.0,
                "observed_score": 20.0,
                "expanded_score": 80.0,
                "tf": 3,
                "df": 2,
                "idf": 4.0,
                "expanded_from": [
                    {
                        "source": "http://example.org/news-es#CrimeAndEvents",
                        "distance": 1,
                        "contribution": 50.0,
                    }
                ],
            }
        ],
    }


def test_find_salience_item_by_full_uri():
    item = find_salience_item(
        sample_salience_data(),
        "http://example.org/news-es#TrafficAccident",
    )

    assert item["label"] == "TrafficAccident"


def test_find_salience_item_by_canonical_uri():
    item = find_salience_item(
        sample_salience_data(),
        "concept_uri:http://example.org/news-es#TrafficAccident",
    )

    assert item["label"] == "TrafficAccident"


def test_find_salience_item_by_short_name():
    item = find_salience_item(
        sample_salience_data(),
        "TrafficAccident",
    )

    assert item["label"] == "TrafficAccident"


def test_find_salience_item_raises_for_missing_target():
    with pytest.raises(ValueError, match="Concept not found"):
        find_salience_item(
            sample_salience_data(),
            "MissingConcept",
        )


def test_explain_salience_item_wraps_context_and_item():
    explanation = explain_salience_item(
        sample_salience_data(),
        "TrafficAccident",
    )

    assert explanation["documents"] == 10
    assert explanation["method"] == "tfidf-e"
    assert explanation["layer"] == "ontology"
    assert explanation["max_distance"] == 2
    assert explanation["decay"] == 0.5
    assert explanation["direction"] == "both"
    assert explanation["item"]["label"] == "TrafficAccident"