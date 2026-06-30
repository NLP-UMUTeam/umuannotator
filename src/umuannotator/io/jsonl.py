import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TextIO

from umuannotator.document import Corpus, Document


@contextmanager
def _open_input(input_path: str) -> Iterator[TextIO]:
    if input_path == "-":
        yield sys.stdin
    else:
        with Path(input_path).open("r", encoding="utf-8") as f:
            yield f


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


def read_jsonl_render_input(input_path: str) -> dict:
    """
    Read annotated JSONL output and wrap it as a renderable corpus dict.

    Each line is expected to be a serialized annotated document.
    """
    documents = []

    with _open_input(input_path) as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            documents.append(json.loads(line))

    return {
        "documents": documents,
        "metadata": {},
    }


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