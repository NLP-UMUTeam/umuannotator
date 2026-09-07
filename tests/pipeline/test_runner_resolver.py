import yaml

from umuannotator.document.model import Annotation
from umuannotator.pipeline.runner import run_from_config


class OverlappingAnnotator:
    def annotate(self, document):
        document.annotations.append(
            Annotation(
                start=0,
                end=9,
                text="@gobierno",
                label="MENTION",
                layer="social",
                source="dummy",
                type="entity",
                subtype="mention",
            )
        )
        document.annotations.append(
            Annotation(
                start=1,
                end=9,
                text="gobierno",
                label="Government",
                layer="ontology",
                source="dummy",
                type="entity",
            )
        )
        return document


def test_run_from_config_applies_resolver_when_enabled(
    tmp_path,
    monkeypatch,
):
    input_path = tmp_path / "input.txt"
    input_path.write_text(
        "@gobierno anuncia ayudas hoy.",
        encoding="utf-8",
    )

    config_path = tmp_path / "config.yml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "ontology": {
                    "language": "es",
                },
                "resolver": {
                    "enabled": True,
                    "strategy": "longest_non_overlapping",
                },
                "annotators": [
                    {
                        "name": "dummy",
                    },
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "umuannotator.pipeline.runner.build_annotators",
        lambda *args, **kwargs: [OverlappingAnnotator()],
    )

    data = run_from_config(
        config_path=str(config_path),
        input_path=str(input_path),
        input_format="text",
        show_progress=False,
    )

    annotations = data["documents"][0]["annotations"]

    assert [
        (
            annotation["text"],
            annotation["layer"],
            annotation["label"],
        )
        for annotation in annotations
    ] == [
        (
            "@gobierno",
            "social",
            "MENTION",
        ),
    ]