import pytest

from umuannotator.metrics.output.payloads import (
    find_salience_item,
    prepare_metric_payload,
    salience_explanation_payload,
    summary_section_payload,
)
from umuannotator.metrics.output.views import MetricOutputView


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


def test_salience_explanation_payload_wraps_context_and_item():
    payload = salience_explanation_payload(
        sample_salience_data(),
        "TrafficAccident",
    )

    assert payload["documents"] == 10
    assert payload["method"] == "tfidf-e"
    assert payload["layer"] == "ontology"
    assert payload["max_distance"] == 2
    assert payload["decay"] == 0.5
    assert payload["direction"] == "both"
    assert payload["item"]["label"] == "TrafficAccident"


def test_summary_section_payload_extracts_rows():
    data = {
        "documents": 2,
        "by_layer": [
            {
                "key": "ontology",
                "count": 4,
            }
        ],
    }

    payload = summary_section_payload(
        data,
        "by_layer",
    )

    assert payload == {
        "metric": "summary",
        "section": "by_layer",
        "rows": [
            {
                "key": "ontology",
                "count": 4,
            }
        ],
    }


def test_summary_section_payload_raises_for_unknown_section():
    with pytest.raises(ValueError, match="Unknown summary section"):
        summary_section_payload(
            {},
            "missing",
        )


def test_prepare_metric_payload_uses_summary_section_view():
    data = {
        "by_layer": [
            {
                "key": "ontology",
                "count": 4,
            }
        ],
    }

    payload = prepare_metric_payload(
        data,
        metric="summary",
        view=MetricOutputView(section="by_layer"),
    )

    assert payload["section"] == "by_layer"


def test_prepare_metric_payload_uses_salience_explain_view():
    payload = prepare_metric_payload(
        sample_salience_data(),
        metric="salience",
        view=MetricOutputView(explain="TrafficAccident"),
    )

    assert payload["item"]["label"] == "TrafficAccident"


def test_prepare_metric_payload_rejects_unknown_metric():
    with pytest.raises(ValueError, match="Unsupported metric"):
        prepare_metric_payload(
            {},
            metric="unknown",
            view=MetricOutputView(),
        )