from pathlib import Path

from umuannotator.io.json import read_json_input
from umuannotator.io.jsonl import read_jsonl_render_input


def infer_render_input_format(input_path: str) -> str:
    if input_path == "-":
        raise ValueError(
            "Cannot infer render input format from stdin. "
            "Use --input-format json or --input-format jsonl."
        )
    
    suffix = Path(input_path).suffix.lower()

    if suffix == ".jsonl":
        return "jsonl"

    if suffix == ".json":
        return "json"

    raise ValueError(
        f"Cannot infer render input format from path: {input_path}. "
        "Use --input-format json or --input-format jsonl."
    )


def read_render_input(
    input_path: str,
    *,
    input_format: str | None = None,
) -> dict:
    resolved_format = input_format or infer_render_input_format(input_path)

    if resolved_format == "json":
        return read_json_input(input_path)

    if resolved_format == "jsonl":
        return read_jsonl_render_input(input_path)

    raise ValueError(f"Unsupported render input format: {resolved_format}")