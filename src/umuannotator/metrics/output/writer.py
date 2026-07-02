from __future__ import annotations

import json
import sys
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