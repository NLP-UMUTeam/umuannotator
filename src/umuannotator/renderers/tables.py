from __future__ import annotations

import json
from typing import Any

from rich.table import Table

from umuannotator.document.model import Document


def document_annotations_table(
    document: Document,
    *,
    title: str = "Annotations",
) -> Table:
    table = Table(
        title=title,
        show_lines=False,
    )

    table.add_column("Span", style="dim", no_wrap=True)
    table.add_column("Text", style="bold")
    table.add_column("Layer")
    table.add_column("Label")
    table.add_column("Type")
    table.add_column("Source")
    table.add_column("Metadata")

    for annotation in sorted(
        document.annotations,
        key=lambda item: (
            item.start,
            item.end,
            item.layer,
            item.label,
        ),
    ):
        table.add_row(
            f"{annotation.start}:{annotation.end}",
            annotation.text,
            annotation.layer,
            annotation.label,
            annotation.type or "",
            _short_source(annotation.source),
            _short_metadata(annotation.metadata),
        )

    return table


def _short_source(source: str | None) -> str:
    if not source:
        return ""

    if "/" in source:
        return source.rstrip("/").rsplit("/", 1)[-1]

    return source


def _short_metadata(metadata: dict[str, Any] | None) -> str:
    if not metadata:
        return ""

    keys = [
        "concept_uri",
        "wikidata",
        "category",
        "rule_id",
        "matched_value",
        "match_type",
        "normalized",
        "grain",
        "unit",
        "duckling_dim",
    ]

    compact = {
        key: metadata[key]
        for key in keys
        if key in metadata
    }

    if not compact:
        return ""

    return json.dumps(
        compact,
        ensure_ascii=False,
    )