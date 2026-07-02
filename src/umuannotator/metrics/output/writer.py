from __future__ import annotations

import json
import sys
import csv
from pathlib import Path
from typing import Any, Callable

from umuannotator.metrics.output.payloads import prepare_metric_payload
from umuannotator.metrics.output.views import MetricOutputView


ConsoleWriter = Callable[[dict[str, Any]], None]


def write_metric_output(
    data: dict[str, Any],
    *,
    metric: str,
    output_format: str = "console",
    output_path: str | None = None,
    view: MetricOutputView | None = None,
    console_writer: ConsoleWriter | None = None,
) -> None:
    payload = prepare_metric_payload(
        data,
        metric=metric,
        view=view or MetricOutputView(),
    )

    if output_format == "console":
        if console_writer is None:
            raise ValueError(
                "console_writer is required for console metric output"
            )

        console_writer(payload)
        return

    if output_format == "json":
        write_json_metric_output(
            payload,
            output_path,
        )
        return
    
    if output_format == "csv":
        write_csv_metric_output(
            payload,
            output_path,
        )
        return

    raise ValueError(f"Unsupported metrics output format: {output_format}")


def write_json_metric_output(
    data: dict[str, Any],
    output_path: str | None = None,
) -> None:
    content = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    )

    if output_path is None or output_path == "-":
        sys.stdout.write(content)
        sys.stdout.write("\n")
        return

    Path(output_path).write_text(
        content + "\n",
        encoding="utf-8",
    )

def write_csv_metric_output(
    data: dict[str, Any],
    output_path: str | None = None,
) -> None:
    rows = data.get("rows")

    if not isinstance(rows, list):
        raise ValueError(
            "CSV metric output requires a tabular payload. "
            "Use --section for metrics summary."
        )

    fieldnames = _fieldnames_from_rows(rows)

    if output_path is None or output_path == "-":
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
        return

    with Path(output_path).open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def _fieldnames_from_rows(
    rows: list[dict[str, Any]],
) -> list[str]:
    fieldnames: list[str] = []

    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    return fieldnames