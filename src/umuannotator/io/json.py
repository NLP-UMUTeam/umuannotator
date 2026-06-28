from __future__ import annotations

import json
import sys
from typing import Any


def read_json_input(input_path: str) -> dict[str, Any]:
    if input_path == "-":
        return json.load(sys.stdin)

    with open(input_path, encoding="utf-8") as f:
        return json.load(f)

def write_json_output(
    data: dict[str, Any],
    output_path: str,
    *,
    indent: int | None = 2,
) -> None:
    f = sys.stdout if output_path == "-" else open(output_path, "w", encoding="utf-8")

    try:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    finally:
        if output_path != "-":
            f.close()