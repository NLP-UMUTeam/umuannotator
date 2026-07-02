from __future__ import annotations

from typing import Any

from umuannotator.metrics.output.helpers import (
    normalize_explain_target,
    shorten_uri,
)
from umuannotator.metrics.output.views import MetricOutputView


SUMMARY_OVERVIEW_KEYS = [
    "documents",
    "documents_with_annotations",
    "documents_without_annotations",
    "annotations",
    "annotations_per_document",
]

def prepare_metric_payload(
    data: dict[str, Any],
    *,
    metric: str,
    view: MetricOutputView,
) -> dict[str, Any]:
    if metric == "summary":
        return prepare_summary_payload(
            data,
            view=view,
        )

    if metric == "salience":
        return prepare_salience_payload(
            data,
            view=view,
        )

    raise ValueError(f"Unsupported metric: {metric}")


def prepare_summary_payload(
    data: dict[str, Any],
    *,
    view: MetricOutputView,
) -> dict[str, Any]:
    if view.section is None:
        return data

    return summary_section_payload(
        data,
        view.section,
    )


def summary_section_payload(
    data: dict[str, Any],
    section: str,
) -> dict[str, Any]:
    if section == "overview":
        return {
            "metric": "summary",
            "section": section,
            "rows": [
                {
                    "metric": key,
                    "value": data.get(key),
                }
                for key in SUMMARY_OVERVIEW_KEYS
                if key in data
            ],
        }

    if section not in data:
        raise ValueError(f"Unknown summary section: {section}")

    rows = data[section]

    if not isinstance(rows, list):
        rows = [
            {
                "key": section,
                "value": rows,
            }
        ]

    return {
        "metric": "summary",
        "section": section,
        "rows": rows,
    }

def prepare_salience_payload(
    data: dict[str, Any],
    *,
    view: MetricOutputView,
) -> dict[str, Any]:
    if view.explain is None:
        return data

    return salience_explanation_payload(
        data,
        view.explain,
    )


def salience_explanation_payload(
    data: dict[str, Any],
    target: str,
) -> dict[str, Any]:
    item = find_salience_item(
        data,
        target,
    )

    return {
        "documents": data.get("documents", 0),
        "method": data.get("method", ""),
        "layer": data.get("layer", ""),
        "max_distance": data.get("max_distance"),
        "decay": data.get("decay"),
        "direction": data.get("direction"),
        "item": item,
    }


def find_salience_item(
    data: dict[str, Any],
    target: str,
) -> dict[str, Any]:
    normalized_target = normalize_explain_target(target)

    for item in data.get("items", []):
        if matches_explain_target(
            item,
            normalized_target,
        ):
            return item

    raise ValueError(f"Concept not found in salience results: {target}")


def matches_explain_target(
    item: dict[str, Any],
    normalized_target: str,
) -> bool:
    concept_uri = str(item.get("concept_uri", ""))
    canonical = str(item.get("canonical", ""))

    candidates = {
        normalize_explain_target(concept_uri),
        normalize_explain_target(canonical),
        normalize_explain_target(shorten_uri(concept_uri)),
        normalize_explain_target(shorten_uri(canonical)),
    }

    return normalized_target in candidates