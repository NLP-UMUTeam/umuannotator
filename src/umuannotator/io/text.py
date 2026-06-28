from __future__ import annotations

import sys
from contextlib import nullcontext

from umuannotator.document import Corpus, Document


def read_text_input(input_path: str) -> Corpus:
    with _open_input(input_path) as f:
        text = f.read().strip()

    return Corpus(
        documents=[
            Document(text=text)
        ]
    )


def _open_input(input_path: str):
    if input_path == "-":
        return nullcontext(sys.stdin)

    return open(input_path, encoding="utf-8")


def write_text_output(
    data: dict,
    output_path: str,
) -> None:
    f = sys.stdout if output_path == "-" else open(output_path, "w", encoding="utf-8")

    try:
        for document in data.get("documents", []):
            f.write(document.get("text", ""))
            f.write("\n")
    finally:
        if output_path != "-":
            f.close()