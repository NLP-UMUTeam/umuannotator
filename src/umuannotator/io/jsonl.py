from __future__ import annotations

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
        with Path(input_path).open(
            "r",
            encoding="utf-8",
        ) as f:
            yield f


def _item_to_document(
    item: dict,
    *,
    idx: int,
    text_column: str,
    id_column: str,
) -> Document:
    document = Document(
        text=str(item[text_column]),
    )

    document.metadata["doc_id"] = item.get(
        id_column,
        idx,
    )
    document.metadata["source"] = item

    return document


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

            documents.append(
                _item_to_document(
                    item,
                    idx=idx,
                    text_column=text_column,
                    id_column=id_column,
                )
            )

    return Corpus(
        documents=documents,
    )


def iter_jsonl_input_batches(
    input_path: str,
    *,
    text_column: str = "text",
    id_column: str = "id",
    batch_size: int = 100,
) -> Iterator[Corpus]:
    documents = []

    with _open_input(input_path) as f:
        for idx, line in enumerate(f):
            line = line.strip()

            if not line:
                continue

            item = json.loads(line)

            documents.append(
                _item_to_document(
                    item,
                    idx=idx,
                    text_column=text_column,
                    id_column=id_column,
                )
            )

            if len(documents) >= batch_size:
                yield Corpus(
                    documents=documents,
                )

                documents = []

    if documents:
        yield Corpus(
            documents=documents,
        )


def read_jsonl_render_input(
    input_path: str,
) -> dict:
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

            documents.append(
                json.loads(line)
            )

    return {
        "documents": documents,
        "metadata": {},
    }


def write_jsonl_output(
    data: dict,
    output_path: str,
    *,
    append: bool = False,
) -> None:
    if output_path == "-":
        f = sys.stdout
    else:
        path = Path(output_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        mode = "a" if append else "w"

        f = path.open(
            mode,
            encoding="utf-8",
        )

    try:
        metadata = data.get(
            "metadata",
            {},
        )

        for document in data.get(
            "documents",
            [],
        ):
            item = {
                "metadata": metadata,
                **document,
            }

            f.write(
                json.dumps(
                    item,
                    ensure_ascii=False,
                )
                + "\n"
            )
    finally:
        if output_path != "-":
            f.close()