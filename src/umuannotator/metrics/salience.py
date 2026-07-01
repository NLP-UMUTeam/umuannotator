from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class SalienceKey:
    layer: str
    label: str
    canonical: str


@dataclass(frozen=True)
class SalienceItem:
    key: SalienceKey
    display: str
    tf: int
    df: int
    idf: float
    score: float


def compute_salience(
    data: dict[str, Any],
    *,
    top: int = 20,
    layer: str | None = None,
    label: str | None = None,
) -> dict[str, Any]:
    documents = data.get("documents", [])
    total_documents = len(documents)

    tf: Counter[SalienceKey] = Counter()
    document_frequency: Counter[SalienceKey] = Counter()
    displays: dict[SalienceKey, Counter[str]] = defaultdict(Counter)

    for document in documents:
        seen_in_document: set[SalienceKey] = set()

        for annotation in document.get("annotations", []):
            if layer is not None and annotation.get("layer") != layer:
                continue

            if label is not None and annotation.get("label") != label:
                continue

            key = annotation_to_salience_key(annotation)

            tf[key] += 1
            seen_in_document.add(key)
            displays[key][str(annotation.get("text", ""))] += 1

        for key in seen_in_document:
            document_frequency[key] += 1

    items = []

    for key, term_frequency in tf.items():
        df = document_frequency[key]
        idf = _idf(
            total_documents=total_documents,
            document_frequency=df,
        )
        score = term_frequency * idf

        items.append(
            SalienceItem(
                key=key,
                display=_most_common_display(displays[key]),
                tf=term_frequency,
                df=df,
                idf=idf,
                score=score,
            )
        )

    items = sorted(
        items,
        key=lambda item: (
            item.score,
            item.tf,
            item.df,
            item.display,
        ),
        reverse=True,
    )

    return {
        "documents": total_documents,
        "items": [
            salience_item_to_dict(item)
            for item in items[:top]
        ],
    }


def annotation_to_salience_key(
    annotation: dict[str, Any],
) -> SalienceKey:
    layer = str(annotation.get("layer", ""))
    label = str(annotation.get("label", ""))
    metadata = annotation.get("metadata", {}) or {}

    canonical = _canonical_value(annotation, metadata)

    return SalienceKey(
        layer=layer,
        label=label,
        canonical=canonical,
    )


def salience_item_to_dict(
    item: SalienceItem,
) -> dict[str, Any]:
    return {
        "layer": item.key.layer,
        "label": item.key.label,
        "canonical": item.key.canonical,
        "display": item.display,
        "tf": item.tf,
        "df": item.df,
        "idf": item.idf,
        "score": item.score,
    }


def _canonical_value(
    annotation: dict[str, Any],
    metadata: dict[str, Any],
) -> str:
    concept_uri = metadata.get("concept_uri")
    if concept_uri:
        return f"concept_uri:{concept_uri}"

    wikidata = metadata.get("wikidata")
    if wikidata:
        return f"wikidata:{wikidata}"

    normalized = metadata.get("normalized")
    if normalized is not None:
        unit = metadata.get("unit")
        grain = metadata.get("grain")

        if unit:
            return f"normalized:{normalized}|unit:{unit}"

        if grain:
            return f"normalized:{normalized}|grain:{grain}"

        return f"normalized:{normalized}"

    text = str(annotation.get("text", ""))

    return f"text:{text.lower().strip()}"


def _idf(
    *,
    total_documents: int,
    document_frequency: int,
) -> float:
    if total_documents <= 0:
        return 0.0

    return math.log(
        (total_documents + 1) / (document_frequency + 1),
    ) + 1


def _most_common_display(
    counter: Counter[str],
) -> str:
    if not counter:
        return ""

    return counter.most_common(1)[0][0]