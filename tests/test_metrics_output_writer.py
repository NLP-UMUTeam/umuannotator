import json

import pytest

from umuannotator.metrics.output.views import MetricOutputView
from umuannotator.metrics.output.writer import (
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