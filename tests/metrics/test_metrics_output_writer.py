import json

import pytest
import csv

from umuannotator.metrics.output.views import MetricOutputView
from umuannotator.metrics.output.writer import (
    write_csv_metric_output,
    write_json_metric_output,
    write_metric_output,
)


def test_write_json_metric_output_to_file(tmp_path):
    path = tmp_path / "metric.json"

    write_json_metric_output(
        {
            "documents": 2,
        },
        str(path),
    )

    data = json.loads(
        path.read_text(encoding="utf-8"),
    )

    assert data == {
        "documents": 2,
    }


def test_write_metric_output_json_applies_view(tmp_path):
    path = tmp_path / "metric.json"

    data = {
        "by_layer": [
            {
                "key": "ontology",
                "count": 4,
            }
        ],
    }

    write_metric_output(
        data,
        metric="summary",
        output_format="json",
        output_path=str(path),
        view=MetricOutputView(section="by_layer"),
    )

    loaded = json.loads(
        path.read_text(encoding="utf-8"),
    )

    assert loaded == {
        "metric": "summary",
        "section": "by_layer",
        "rows": [
            {
                "key": "ontology",
                "count": 4,
            }
        ],
    }


def test_write_metric_output_console_uses_console_writer():
    calls = []

    def console_writer(payload):
        calls.append(payload)

    write_metric_output(
        {
            "documents": 2,
        },
        metric="summary",
        output_format="console",
        console_writer=console_writer,
    )

    assert calls == [
        {
            "documents": 2,
        }
    ]


def test_write_metric_output_console_requires_writer():
    with pytest.raises(ValueError, match="console_writer is required"):
        write_metric_output(
            {},
            metric="summary",
            output_format="console",
        )


def test_write_metric_output_rejects_unknown_format():
    with pytest.raises(ValueError, match="Unsupported metrics output format"):
        write_metric_output(
            {},
            metric="summary",
            output_format="xml",
        )

def test_write_csv_metric_output_to_file(tmp_path):
    path = tmp_path / "metric.csv"

    write_csv_metric_output(
        {
            "rows": [
                {
                    "key": "ontology",
                    "count": 4,
                },
                {
                    "key": "temporal",
                    "count": 2,
                },
            ],
        },
        str(path),
    )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        rows = list(csv.DictReader(f))

    assert rows == [
        {
            "key": "ontology",
            "count": "4",
        },
        {
            "key": "temporal",
            "count": "2",
        },
    ]


def test_write_metric_output_csv_applies_summary_section_view(tmp_path):
    path = tmp_path / "summary.csv"

    data = {
        "by_layer": [
            {
                "key": "ontology",
                "count": 4,
            }
        ],
    }

    write_metric_output(
        data,
        metric="summary",
        output_format="csv",
        output_path=str(path),
        view=MetricOutputView(section="by_layer"),
    )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        rows = list(csv.DictReader(f))

    assert rows == [
        {
            "key": "ontology",
            "count": "4",
        }
    ]


def test_write_metric_output_csv_requires_tabular_payload():
    with pytest.raises(ValueError, match="CSV metric output requires"):
        write_metric_output(
            {
                "documents": 2,
            },
            metric="summary",
            output_format="csv",
            view=MetricOutputView(),
        )

def test_write_metric_output_csv_supports_salience_items(tmp_path):
    path = tmp_path / "salience.csv"

    data = {
        "method": "tfidf",
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

    write_metric_output(
        data,
        metric="salience",
        output_format="csv",
        output_path=str(path),
    )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        rows = list(csv.DictReader(f))

    assert rows == [
        {
            "score": "3.5",
            "tf": "2",
            "df": "1",
            "idf": "1.75",
            "layer": "ontology",
            "label": "Politics",
            "display": "Gobierno",
            "canonical": "concept_uri:http://example.org#Politics",
        }
    ]

def test_write_metric_output_html_to_file(tmp_path):
    path = tmp_path / "salience.html"

    write_metric_output(
        {
            "method": "tfidf",
            "documents": 1,
            "items": [
                {
                    "score": 1.0,
                    "tf": 1,
                    "df": 1,
                    "idf": 1.0,
                    "layer": "ontology",
                    "label": "Politics",
                    "display": "Gobierno",
                    "canonical": "concept_uri:http://example.org#Politics",
                }
            ],
        },
        metric="salience",
        output_format="html",
        output_path=str(path),
    )

    html = path.read_text(encoding="utf-8")

    assert "<!doctype html>" in html
    assert "Annotation salience" in html
    assert "Gobierno" in html


def test_write_metric_output_html_supports_summary(tmp_path):
    path = tmp_path / "summary.html"

    write_metric_output(
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
            "by_label": [],
            "by_layer_label": [],
            "top_annotations": [],
        },
        metric="summary",
        output_format="html",
        output_path=str(path),
    )

    html = path.read_text(encoding="utf-8")

    assert "<!doctype html>" in html
    assert "Annotation summary" in html
    assert "ontology" in html