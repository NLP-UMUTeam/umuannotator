import json

from umuannotator.pipeline.runner import run_from_config


def test_batched_run_creates_workspace(
    tmp_path,
):
    config_path = tmp_path / "config.yml"
    input_path = tmp_path / "input.jsonl"
    output_path = tmp_path / "output.jsonl"

    config_path.write_text(
        """
ontology:
  language: en

annotators: []

metrics:
  tfidf:
    enabled: false

  extended_tfidf:
    enabled: false
""",
        encoding="utf-8",
    )

    with input_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        for idx in range(205):
            f.write(
                json.dumps(
                    {
                        "id": idx,
                        "text": f"document {idx}",
                    }
                )
                + "\n"
            )

    summary = run_from_config(
        config_path=str(config_path),
        input_path=str(input_path),
        output_path=str(output_path),
        input_format="jsonl",
        output_format="jsonl",
        batch_size=100,
        show_progress=False,
    )

    assert summary["documents"] == 205
    assert summary["batches"] == 3

    assert output_path.exists()

    work_dir = tmp_path / "output.jsonl.work"

    assert work_dir.is_dir()

    state_path = (
        work_dir / "state.json"
    )

    assert state_path.exists()

    stage1 = (
        work_dir / "stage1"
    )

    stage1_batches = sorted(
        stage1.glob(
            "batch_*.jsonl"
        )
    )

    assert len(stage1_batches) == 3

    assert [
        batch.name
        for batch in stage1_batches
    ] == [
        "batch_000001.jsonl",
        "batch_000002.jsonl",
        "batch_000003.jsonl",
    ]

    assert not list(
        stage1.glob(
            "*.tmp"
        )
    )

    state = json.loads(
        state_path.read_text(
            encoding="utf-8"
        )
    )

    assert state[
        "stage1_complete"
    ] is True

    assert state[
        "completed"
    ] is True

    assert state[
        "status"
    ] == "completed"

    assert (
        len(
            output_path.read_text(
                encoding="utf-8"
            ).splitlines()
        )
        == 205
    )

def test_batched_run_with_metrics_creates_stage2(
    tmp_path,
):
    config_path = tmp_path / "config.yml"
    input_path = tmp_path / "input.jsonl"
    output_path = tmp_path / "output.jsonl"

    config_path.write_text(
        """
ontology:
  language: en

annotators: []

metrics:
  tfidf:
    enabled: true
    layer: ontology

  extended_tfidf:
    enabled: false
""",
        encoding="utf-8",
    )

    with input_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        for idx in range(205):
            f.write(
                json.dumps(
                    {
                        "id": idx,
                        "text": f"document {idx}",
                    }
                )
                + "\n"
            )

    summary = run_from_config(
        config_path=str(config_path),
        input_path=str(input_path),
        output_path=str(output_path),
        input_format="jsonl",
        output_format="jsonl",
        batch_size=100,
        show_progress=False,
        output_profile="full",
    )

    assert summary["documents"] == 205
    assert summary["batches"] == 3

    work_dir = (
        tmp_path
        / "output.jsonl.work"
    )

    stage1_batches = sorted(
        (
            work_dir / "stage1"
        ).glob(
            "batch_*.jsonl"
        )
    )

    stage2_batches = sorted(
        (
            work_dir / "stage2"
        ).glob(
            "batch_*.jsonl"
        )
    )

    assert len(
        stage1_batches
    ) == 3

    assert len(
        stage2_batches
    ) == 3

    assert not list(
        (
            work_dir / "stage2"
        ).glob(
            "*.tmp"
        )
    )

    state = json.loads(
        (
            work_dir
            / "state.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert state[
        "stage1_complete"
    ] is True

    assert state[
        "stage2_complete"
    ] is True

    assert state[
        "completed"
    ] is True

    assert (
        len(
            output_path.read_text(
                encoding="utf-8"
            ).splitlines()
        )
        == 205
    )