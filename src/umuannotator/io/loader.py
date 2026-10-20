from __future__ import annotations

from pathlib import Path
from typing import Iterator

from umuannotator.document import Corpus
from umuannotator.io.csv import read_csv_input
from umuannotator.io.jsonl import (
    iter_jsonl_input_batches,
    read_jsonl_input,
)
from umuannotator.io.text import read_text_input


def infer_input_format(
    input_path: str,
    input_format: str | None = None,
) -> str:
    if input_format:
        return input_format

    if input_path == "-":
        return "text"

    suffix = Path(input_path).suffix.lower()

    if suffix == ".csv":
        return "csv"

    if suffix in {
        ".jsonl",
        ".ndjson",
    }:
        return "jsonl"

    if suffix in {
        ".txt",
        ".text",
    }:
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
    input_format = infer_input_format(
        input_path,
        input_format,
    )

    if input_format == "csv":
        return read_csv_input(
            input_path,
            text_column=text_column,
            sep=sep,
        )

    if input_format == "jsonl":
        return read_jsonl_input(
            input_path,
            text_column=text_column,
            id_column=id_column,
        )

    if input_format == "text":
        return read_text_input(
            input_path,
        )

    raise ValueError(
        f"Unsupported input format: "
        f"{input_format}"
    )


def iter_corpus_input_batches(
    input_path: str,
    *,
    input_format: str | None = None,
    text_column: str = "text",
    id_column: str = "id",
    sep: str = ",",
    batch_size: int = 100,
) -> Iterator[Corpus]:
    input_format = infer_input_format(
        input_path,
        input_format,
    )

    if input_format == "jsonl":
        yield from iter_jsonl_input_batches(
            input_path,
            text_column=text_column,
            id_column=id_column,
            batch_size=batch_size,
        )

        return

    # CSV/text still use the current reader for now.
    # They can be made streaming later if needed.
    corpus = load_corpus_input(
        input_path,
        input_format=input_format,
        text_column=text_column,
        id_column=id_column,
        sep=sep,
    )

    documents = corpus.documents

    for start in range(
        0,
        len(documents),
        batch_size,
    ):
        yield Corpus(
            documents=documents[
                start:start + batch_size
            ],
        )

def count_corpus_input_documents(
    input_path: str,
    *,
    input_format: str | None = None,
    text_column: str = "text",
    id_column: str = "id",
    sep: str = ",",
) -> int | None:
    """
    Return the number of documents in an input corpus.

    Returns None when the input is stdin because counting it
    beforehand would consume the stream.
    """
    if input_path == "-":
        return None

    resolved_format = infer_input_format(
        input_path,
        input_format,
    )

    if resolved_format == "jsonl":
        with Path(input_path).open(
            "r",
            encoding="utf-8",
        ) as f:
            return sum(
                1
                for line in f
                if line.strip()
            )

    # For formats whose document semantics are already defined
    # by their readers, reuse the existing loader.
    corpus = load_corpus_input(
        input_path,
        input_format=resolved_format,
        text_column=text_column,
        id_column=id_column,
        sep=sep,
    )

    return len(
        corpus.documents
    )