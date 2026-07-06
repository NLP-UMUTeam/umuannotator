import pytest

from umuannotator.metrics.output.html import render_html_metric_output


def test_render_salience_html_contains_basic_items():
    html = render_html_metric_output(
        {
            "method": "tfidf",
            "documents": 2,
            "items": [
                {
                    "score": 3.5,
                    "tf": 2,
                    "df": 1,
                    "idf": 1.75,
                    "layer": "ontology",
                    "label": "Politics",
                    "display": "Gobierno",
                    "canonical": "concept_uri:http://example.org#Politics",
                }
            ],
        }
    )

    assert "Annotation salience" in html
    assert "Gobierno" in html
    assert "Politics" in html
    assert "3.500" in html


def test_render_salience_html_contains_tfidfe_scores():
    html = render_html_metric_output(
        {
            "metric": "salience",
            "method": "tfidf-e",
            "documents": 2,
            "layer": "ontology",
            "max_distance": 2,
            "decay": 0.5,
            "direction": "both",
            "items": [
                {
                    "score": 10.0,
                    "observed_score": 2.0,
                    "expanded_score": 8.0,
                    "tf": 1,
                    "df": 1,
                    "idf": 2.0,
                    "layer": "ontology",
                    "label": "TrafficAccident",
                    "display": "carretera",
                    "canonical": "concept_uri:http://example.org#TrafficAccident",
                    "concept_uri": "http://example.org#TrafficAccident",
                    "expanded_from": [
                        {
                            "source": "http://example.org#CrimeAndEvents",
                            "distance": 1,
                            "contribution": 8.0,
                        }
                    ],
                }
            ],
        }
    )

    assert "tfidf-e" in html
    assert "TrafficAccident" in html
    assert "carretera" in html
    assert "2.000" in html
    assert "8.000" in html
    assert "80.0%" in html
    assert "CrimeAndEvents" in html
    assert "1 contributions" in html


def test_render_html_metric_output_rejects_unsupported_payload():
    with pytest.raises(ValueError, match="supported only for summary and salience"):
        render_html_metric_output(
            {
                "metric": "unknown",
                "rows": [],
            }
        )