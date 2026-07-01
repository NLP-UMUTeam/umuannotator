import json

from umuannotator.metrics.output import write_metrics_json


def test_write_metrics_json_to_file(tmp_path):
    path = tmp_path / "summary.json"

    write_metrics_json(
        {
            "documents": 2,
            "annotations": 3,
        },
        str(path),
    )

    data = json.loads(path.read_text(encoding="utf-8"))

    assert data == {
        "documents": 2,
        "annotations": 3,
    }