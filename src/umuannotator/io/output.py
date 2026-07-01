from pathlib import Path
from typing import Any

from umuannotator.io.json import write_json_output
from umuannotator.io.jsonl import write_jsonl_output
from umuannotator.io.text import write_text_output
from umuannotator.serialization.profiles import apply_output_profile


def infer_output_format(output_path: str, output_format: str | None = None) -> str:
    if output_format:
        return output_format

    if output_path == "-":
        return "jsonl"

    suffix = Path(output_path).suffix.lower()

    if suffix == ".json":
        return "json"

    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"

    if suffix in {".txt", ".text"}:
        return "text"

    return "json"


def write_output(
    data: dict[str, Any],
    output_path: str,
    *,
    output_format: str | None = None,
    output_profile: str = "compact",
) -> None:
    output_format = infer_output_format(output_path, output_format)

    serialized_data = apply_output_profile(
        data,
        profile=output_profile,
    )

    if output_format == "json":
        write_json_output(serialized_data, output_path)
        return

    if output_format == "jsonl":
        write_jsonl_output(serialized_data, output_path)
        return

    if output_format == "text":
        write_text_output(serialized_data, output_path)
        return

    raise ValueError(f"Unsupported output format: {output_format}")