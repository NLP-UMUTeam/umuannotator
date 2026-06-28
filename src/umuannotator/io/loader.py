from __future__ import annotations
from pathlib import Path

from umuannotator.document import Corpus
from umuannotator.io.csv import read_csv_input
from umuannotator.io.jsonl import read_jsonl_input
from umuannotator.io.text import read_text_input


def infer_input_format(input_path: str, input_format: str | None = None) -> str:
    if input_format:
        return input_format

    if input_path == "-":
        return "text"

    suffix = Path(input_path).suffix.lower()

    if suffix == ".csv":
        return "csv"

    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"

    if suffix in {".txt", ".text"}:
        return "text"

    return "csv"


def load_corpus_input(
    input_path: str,
    *,
    input_format: str | None = None,
    text_column: str = "text",
    id_column: str = "id",
    sep: str = ",",
) -> Corpus:
    input_format = infer_input_format(input_path, input_format)

    if input_format == "csv":
        return read_csv_input(input_path, text_column=text_column, sep=sep)

    if input_format == "jsonl":
        return read_jsonl_input(input_path, text_column=text_column, id_column=id_column)

    if input_format == "text":
        return read_text_input(input_path)

    raise ValueError(f"Unsupported input format: {input_format}")
