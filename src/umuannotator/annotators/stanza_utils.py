from __future__ import annotations

from typing import Any

from umuannotator.document.model import Document


def find_stanza_token(
    document: Document,
    *,
    start: int,
    end: int,
) -> dict[str, Any] | None:
    stanza = document.metadata.get("stanza")

    if not stanza:
        return None

    for token in stanza.get("tokens", []):
        if token.get("start") == start and token.get("end") == end:
            return token

    return None


def find_stanza_entity_containing(
    document: Document,
    *,
    start: int,
    end: int,
) -> dict[str, Any] | None:
    stanza = document.metadata.get("stanza")

    if not stanza:
        return None

    for entity in stanza.get("entities", []):
        entity_start = entity.get("start")
        entity_end = entity.get("end")

        if entity_start is None or entity_end is None:
            continue

        if start >= entity_start and end <= entity_end:
            return entity

    return None