from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def write_metrics_json(
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