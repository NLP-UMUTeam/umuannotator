from __future__ import annotations

import json
import sys
from contextlib import nullcontext

from umuannotator.document import Corpus, Document


def read_jsonl_input(
    input_path: str,
    *,
    text_column: str = "text",
    id_column: str = "id",
) -> Corpus:
    documents = []

    with _open_input(input_path) as f:
        for idx, line in enumerate(f):
            line = line.strip()

            if not line:
                continue

            item = json.loads(line)

            document = Document(
                text=str(item[text_column]),
            )

            document.metadata["doc_id"] = item.get(id_column, idx)
            document.metadata["source"] = item

            documents.append(document)

    return Corpus(documents=documents)


def _open_input(input_path: str):
    if input_path == "-":
        return nullcontext(sys.stdin)

    return open(input_path, encoding="utf-8")


def write_jsonl_output(
    data: dict,
    output_path: str,
) -> None:
    f = sys.stdout if output_path == "-" else open(output_path, "w", encoding="utf-8")

    try:
        metadata = data.get("metadata", {})

        for document in data.get("documents", []):
            item = {
                "metadata": metadata,
                **document,
            }
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    finally:
        if output_path != "-":
            f.close()