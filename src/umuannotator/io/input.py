from __future__ import annotations

import json
import sys

import pandas as pd

from umuannotator.document import Corpus, Document
from umuannotator.io.dataframe import dataframe_to_corpus


def read_corpus_input(
    input_path: str,
    *,
    input_format: str = "csv",
    text_column: str = "text",
    sep: str = ",",
) -> Corpus:
    if input_format == "csv":
        source = sys.stdin if input_path == "-" else input_path
        df = pd.read_csv(source, sep=sep)

        return dataframe_to_corpus(
            df,
            text_column=text_column,
        )

    if input_format == "jsonl":
        documents = []

        with _open_text_input(input_path) as f:
            for idx, line in enumerate(f):
                if not line.strip():
                    continue

                item = json.loads(line)
                document = Document(text=str(item[text_column]))
                document.metadata["doc_id"] = item.get("id", idx)
                document.metadata["source"] = item
                documents.append(document)

        return Corpus(documents=documents)

    if input_format == "text":
        with _open_text_input(input_path) as f:
            text = f.read().strip()

        return Corpus(
            documents=[
                Document(text=text)
            ]
        )

    raise ValueError(f"Unsupported input format: {input_format}")


def _open_text_input(input_path: str):
    if input_path == "-":
        return sys.stdin

    return open(input_path, encoding="utf-8")