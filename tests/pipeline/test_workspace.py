import json

from umuannotator.pipeline.workspace import (
    assemble_batches,
    build_workspace_paths,
    initialize_workspace,
    read_state,
    write_batch_atomic,
    list_completed_batches
)


def test_build_workspace_paths(
    tmp_path,
):
    output_path = (
        tmp_path / "result.jsonl"
    )

    paths = build_workspace_paths(
        str(output_path)
    )

    assert paths.output == output_path

    assert paths.work_dir == (
        tmp_path / "result.jsonl.work"
    )

    assert paths.state == (
        tmp_path
        / "result.jsonl.work"
        / "state.json"
    )


def test_initialize_workspace(
    tmp_path,
):
    output_path = (
        tmp_path / "result.jsonl"
    )

    paths = initialize_workspace(
        str(output_path),
        batch_size=100,
    )

    assert paths.work_dir.is_dir()
    assert paths.stage1.is_dir()
    assert paths.stage2.is_dir()
    assert paths.state.is_file()

    state = read_state(
        paths
    )

    assert state["version"] == 1
    assert state["status"] == "running"
    assert state["batch_size"] == 100
    assert state["stage1_complete"] is False
    assert state["stage2_required"] is False
    assert state["stage2_complete"] is True
    assert state["completed"] is False


def test_write_batch_atomic(
    tmp_path,
):
    output_path = (
        tmp_path / "result.jsonl"
    )

    paths = initialize_workspace(
        str(output_path),
        batch_size=100,
    )

    batch = write_batch_atomic(
        paths.stage1,
        1,
        [
            '{"id": 1}',
            '{"id": 2}',
        ],
    )

    assert batch.is_file()

    assert batch.name == (
        "batch_000001.jsonl"
    )

    assert not (
        paths.stage1
        / "batch_000001.jsonl.tmp"
    ).exists()

    assert batch.read_text(
        encoding="utf-8",
    ) == (
        '{"id": 1}\n'
        '{"id": 2}\n'
    )


def test_assemble_batches(
    tmp_path,
):
    output_path = (
        tmp_path / "result.jsonl"
    )

    paths = initialize_workspace(
        str(output_path),
        batch_size=2,
    )

    write_batch_atomic(
        paths.stage1,
        1,
        [
            '{"id": 1}',
            '{"id": 2}',
        ],
    )

    write_batch_atomic(
        paths.stage1,
        2,
        [
            '{"id": 3}',
        ],
    )

    assembled = assemble_batches(
        paths.stage1,
        output_path,
    )

    assert assembled == output_path

    assert output_path.read_text(
        encoding="utf-8",
    ) == (
        '{"id": 1}\n'
        '{"id": 2}\n'
        '{"id": 3}\n'
    )


def test_initialize_workspace_with_stage2(
    tmp_path,
):
    output_path = (
        tmp_path / "result.jsonl"
    )

    paths = initialize_workspace(
        str(output_path),
        batch_size=100,
        stage2_required=True,
    )

    state = read_state(
        paths
    )

    assert state["stage2_required"] is True
    assert state["stage2_complete"] is False


def test_initialize_workspace_resume(
    tmp_path,
):
    output_path = (
        tmp_path / "result.jsonl"
    )

    initialize_workspace(
        str(output_path),
        batch_size=100,
        stage2_required=True,
    )

    paths = initialize_workspace(
        str(output_path),
        batch_size=100,
        stage2_required=True,
        resume=True,
    )

    assert paths.work_dir.exists()
    assert paths.state.exists()


def test_list_completed_batches(
    tmp_path,
):
    output_path = (
        tmp_path / "result.jsonl"
    )

    paths = initialize_workspace(
        str(output_path),
        batch_size=100,
    )

    write_batch_atomic(
        paths.stage1,
        1,
        ['{"id": 1}'],
    )

    write_batch_atomic(
        paths.stage1,
        3,
        ['{"id": 3}'],
    )

    # This must not count as a completed batch.
    (
        paths.stage1
        / "batch_000002.jsonl.tmp"
    ).write_text(
        '{"id": 2}\n',
        encoding="utf-8",
    )

    assert list_completed_batches(
        paths.stage1
    ) == {
        1,
        3,
    }


import pytest


def test_resume_rejects_different_batch_size(
    tmp_path,
):
    output_path = (
        tmp_path / "result.jsonl"
    )

    initialize_workspace(
        str(output_path),
        batch_size=100,
    )

    with pytest.raises(
        ValueError,
        match="batch size",
    ):
        initialize_workspace(
            str(output_path),
            batch_size=50,
            resume=True,
        )