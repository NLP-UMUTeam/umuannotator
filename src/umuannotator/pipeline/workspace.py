from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


WORKSPACE_VERSION = 1


@dataclass(frozen=True)
class WorkspacePaths:
    output: Path
    work_dir: Path
    state: Path
    stage1: Path
    stage2: Path


def build_workspace_paths(
    output_path: str,
) -> WorkspacePaths:
    output = Path(output_path)

    work_dir = output.with_name(
        output.name + ".work"
    )

    return WorkspacePaths(
        output=output,
        work_dir=work_dir,
        state=work_dir / "state.json",
        stage1=work_dir / "stage1",
        stage2=work_dir / "stage2",
    )


def initialize_workspace(
    output_path: str,
    *,
    batch_size: int,
    stage2_required: bool = False,
    resume: bool = False,
) -> WorkspacePaths:
    paths = build_workspace_paths(
        output_path
    )

    if resume:
        if not paths.work_dir.exists():
            raise FileNotFoundError(
                f"Cannot resume: workspace does not exist: "
                f"{paths.work_dir}"
            )

        if not paths.state.exists():
            raise FileNotFoundError(
                f"Cannot resume: workspace state does not exist: "
                f"{paths.state}"
            )

        state = read_state(
            paths
        )

        if state.get("version") != WORKSPACE_VERSION:
            raise ValueError(
                "Cannot resume: incompatible workspace version."
            )

        if state.get("batch_size") != batch_size:
            raise ValueError(
                "Cannot resume: batch size does not match "
                "the existing workspace."
            )

        if state.get(
            "stage2_required",
            False,
        ) != stage2_required:
            raise ValueError(
                "Cannot resume: metric configuration does not match "
                "the existing workspace."
            )

        paths.stage1.mkdir(
            parents=True,
            exist_ok=True,
        )

        paths.stage2.mkdir(
            parents=True,
            exist_ok=True,
        )

        return paths

    if paths.work_dir.exists():
        shutil.rmtree(
            paths.work_dir
        )

    paths.stage1.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths.stage2.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_state(
        paths,
        {
            "version": WORKSPACE_VERSION,
            "status": "running",
            "batch_size": batch_size,
            "stage1_complete": False,
            "stage2_required": stage2_required,
            "stage2_complete": (
                not stage2_required
            ),
            "completed": False,
        },
    )

    return paths


def list_completed_batches(
    directory: Path,
) -> set[int]:
    completed = set()

    for path in directory.glob(
        "batch_*.jsonl"
    ):
        stem = path.stem

        try:
            batch_index = int(
                stem.removeprefix(
                    "batch_"
                )
            )
        except ValueError:
            continue

        completed.add(
            batch_index
        )

    return completed


def batch_path(
    directory: Path,
    batch_index: int,
) -> Path:
    return directory / (
        f"batch_{batch_index:06d}.jsonl"
    )


def write_batch_atomic(
    directory: Path,
    batch_index: int,
    lines: Iterable[str],
) -> Path:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_path = batch_path(
        directory,
        batch_index,
    )

    tmp_path = final_path.with_suffix(
        final_path.suffix + ".tmp"
    )

    with tmp_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        for line in lines:
            if not line.endswith("\n"):
                line += "\n"

            f.write(line)

        f.flush()
        os.fsync(
            f.fileno()
        )

    os.replace(
        tmp_path,
        final_path,
    )

    return final_path


def assemble_batches(
    batch_directory: Path,
    output_path: str | Path,
) -> Path:
    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    tmp_output = output.with_suffix(
        output.suffix + ".tmp"
    )

    batch_files = sorted(
        batch_directory.glob(
            "batch_*.jsonl"
        )
    )

    with tmp_output.open(
        "w",
        encoding="utf-8",
    ) as target:
        for batch_file in batch_files:
            with batch_file.open(
                "r",
                encoding="utf-8",
            ) as source:
                for line in source:
                    target.write(line)

        target.flush()
        os.fsync(
            target.fileno()
        )

    os.replace(
        tmp_output,
        output,
    )

    return output


def write_state(
    paths: WorkspacePaths,
    state: dict[str, Any],
) -> None:
    paths.work_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    tmp_path = paths.state.with_suffix(
        ".json.tmp"
    )

    with tmp_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

        f.write("\n")
        f.flush()
        os.fsync(
            f.fileno()
        )

    os.replace(
        tmp_path,
        paths.state,
    )


def read_state(
    paths: WorkspacePaths,
) -> dict[str, Any]:
    with paths.state.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)