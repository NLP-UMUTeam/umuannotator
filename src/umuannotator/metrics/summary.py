from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AnnotationKey:
    text: str
    layer: str
    label: str


def summarize_annotations(
    data: dict[str, Any],
    *,
    top: int = 20,
) -> dict[str, Any]:
    documents = data.get("documents", [])

    total_documents = len(documents)
    documents_with_annotations = 0
    total_annotations = 0

    by_layer: Counter[str] = Counter()
    by_label: Counter[str] = Counter()
    by_layer_label: Counter[tuple[str, str]] = Counter()
    by_annotation: Counter[AnnotationKey] = Counter()

    for document in documents:
        annotations = document.get("annotations", [])

        if annotations:
            documents_with_annotations += 1

        total_annotations += len(annotations)

        for annotation in annotations:
            text = str(annotation.get("text", ""))
            layer = str(annotation.get("layer", ""))
            label = str(annotation.get("label", ""))

            by_layer[layer] += 1
            by_label[label] += 1
            by_layer_label[(layer, label)] += 1
            by_annotation[
                AnnotationKey(
                    text=text,
                    layer=layer,
                    label=label,
                )
            ] += 1

    documents_without_annotations = (
        total_documents - documents_with_annotations
    )

    annotations_per_document = (
        total_annotations / total_documents
        if total_documents
        else 0.0
    )

    return {
        "documents": total_documents,
        "documents_with_annotations": documents_with_annotations,
        "documents_without_annotations": documents_without_annotations,
        "annotations": total_annotations,
        "annotations_per_document": annotations_per_document,
        "by_layer": _counter_to_rows(by_layer, top=top),
        "by_label": _counter_to_rows(by_label, top=top),
        "by_layer_label": _layer_label_to_rows(
            by_layer_label,
            top=top,
        ),
        "top_annotations": _annotations_to_rows(
            by_annotation,
            top=top,
        ),
    }


def _counter_to_rows(
    counter: Counter[str],
    *,
    top: int,
) -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "count": count,
        }
        for key, count in counter.most_common(top)
    ]


def _layer_label_to_rows(
    counter: Counter[tuple[str, str]],
    *,
    top: int,
) -> list[dict[str, Any]]:
    return [
        {
            "layer": layer,
            "label": label,
            "count": count,
        }
        for (layer, label), count in counter.most_common(top)
    ]


def _annotations_to_rows(
    counter: Counter[AnnotationKey],
    *,
    top: int,
) -> list[dict[str, Any]]:
    return [
        {
            "text": key.text,
            "layer": key.layer,
            "label": key.label,
            "count": count,
        }
        for key, count in counter.most_common(top)
    ]