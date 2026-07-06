from umuannotator.metrics.output.html import render_html_metric_output


def test_render_summary_html_contains_overview_and_sections():
    html = render_html_metric_output(
        {
            "documents": 10,
            "documents_with_annotations": 8,
            "documents_without_annotations": 2,
            "annotations": 25,
            "annotations_per_document": 2.5,
            "by_layer": [
                {
                    "layer": "ontology",
                    "count": 12,
                }
            ],
            "by_label": [
                {
                    "label": "Politics",
                    "count": 5,
                }
            ],
            "by_layer_label": [
                {
                    "layer": "ontology",
                    "label": "Politics",
                    "count": 5,
                }
            ],
            "top_annotations": [
                {
                    "text": "Gobierno",
                    "label": "Politics",
                    "count": 3,
                }
            ],
        }
    )

    assert "Annotation summary" in html
    assert "Documents" in html
    assert "10" in html
    assert "By layer" in html
    assert "ontology" in html
    assert "Politics" in html
    assert "Gobierno" in html


def test_render_summary_html_supports_section_payload():
    html = render_html_metric_output(
        {
            "metric": "summary",
            "section": "by_layer",
            "rows": [
                {
                    "layer": "ontology",
                    "count": 12,
                }
            ],
        }
    )

    assert "Annotation summary · by_layer" in html
    assert "By Layer" in html
    assert "ontology" in html
    assert "12" in html