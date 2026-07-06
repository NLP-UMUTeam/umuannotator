from __future__ import annotations

from html import escape
from importlib.resources import files
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from umuannotator.metrics.output.helpers import (
    format_float,
    format_percent,
    shorten_uri,
)


def render_html_metric_output(
    data: dict[str, Any],
) -> str:
    metric = data.get("metric")

    if metric == "salience" or "items" in data:
        return render_salience_html(data)

    if metric == "summary" or _looks_like_summary(data):
        return render_summary_html(data)

    raise ValueError(
        "HTML metric output is currently supported only for summary "
        "and salience."
    )


def render_salience_html(
    data: dict[str, Any],
) -> str:
    env = _template_environment()
    template = env.get_template("salience.html.j2")

    context = salience_template_context(data)

    return template.render(**context)


def salience_template_context(
    data: dict[str, Any],
) -> dict[str, Any]:
    items = data.get("items")

    if items is None and "rows" in data:
        items = data.get("rows", [])

    items = items or []

    extended = any(
        "observed_score" in item or "expanded_score" in item
        for item in items
    )

    return {
        "title": "Annotation salience",
        "metadata": _metadata_items(data),
        "method": data.get("method", "tfidf"),
        "extended": extended,
        "items": [
            _salience_item_context(item)
            for item in items
        ],
    }


def _metadata_items(
    data: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = [
        ("Method", data.get("method", "tfidf")),
        ("Documents", data.get("documents")),
        ("Layer", data.get("layer")),
        ("Max distance", data.get("max_distance")),
        ("Decay", data.get("decay")),
        ("Direction", data.get("direction")),
    ]

    return [
        {
            "key": key,
            "value": value,
        }
        for key, value in rows
        if value is not None and value != ""
    ]


def _salience_item_context(
    item: dict[str, Any],
) -> dict[str, Any]:
    concept = item.get("concept_uri") or item.get("canonical") or ""

    return {
        "score": item.get("score", 0.0),
        "observed_score": item.get("observed_score", 0.0),
        "expanded_score": item.get("expanded_score", 0.0),
        "tf": item.get("tf"),
        "df": item.get("df"),
        "idf": item.get("idf"),
        "layer": item.get("layer"),
        "label": item.get("label"),
        "display": item.get("display"),
        "concept": shorten_uri(str(concept)),
        "expanded_from": [
            _expanded_from_context(source)
            for source in item.get("expanded_from", []) or []
        ],
    }


def _expanded_from_context(
    source: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source": source.get("source", ""),
        "source_label": shorten_uri(str(source.get("source", ""))),
        "distance": source.get("distance", ""),
        "contribution": source.get("contribution", 0.0),
    }


def _template_environment() -> Environment:
    template_dir = (
        files("umuannotator.metrics.output")
        / "templates"
    )

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml", "j2"]),
    )

    env.filters["fmt_float"] = format_float
    env.filters["fmt_percent"] = _format_percent_filter
    env.globals["score_bar"] = _score_bar

    return env


def _format_percent_filter(
    value: float,
    total: float,
) -> str:
    return format_percent(
        float(value or 0.0),
        float(total or 0.0),
    )


def _score_bar(
    value: float,
    total: float,
) -> str:
    value = float(value or 0.0)
    total = float(total or 0.0)

    if total <= 0:
        percent = 0.0
    else:
        percent = max(
            0.0,
            min(
                100.0,
                (value / total) * 100,
            ),
        )

    return f"""
    <div class="score-bar">
      <div class="score-bar-fill" style="width: {percent:.1f}%"></div>
      <span>{escape(format_float(value))}</span>
    </div>
    """


def render_summary_html(
    data: dict[str, Any],
) -> str:
    env = _template_environment()
    template = env.get_template("summary.html.j2")

    context = summary_template_context(data)

    return template.render(**context)


def summary_template_context(
    data: dict[str, Any],
) -> dict[str, Any]:
    if "rows" in data and data.get("section"):
        return _summary_section_context(data)

    return {
        "title": "Annotation summary",
        "overview": _summary_overview(data),
        "sections": [
            _summary_table_section(
                title="By layer",
                rows=data.get("by_layer", []),
            ),
            _summary_table_section(
                title="By label",
                rows=data.get("by_label", []),
            ),
            _summary_table_section(
                title="By layer and label",
                rows=data.get("by_layer_label", []),
            ),
            _summary_table_section(
                title="Top annotations",
                rows=data.get("top_annotations", []),
            ),
        ],
    }


def _summary_section_context(
    data: dict[str, Any],
) -> dict[str, Any]:
    section = str(data.get("section", ""))

    return {
        "title": f"Annotation summary · {section}",
        "overview": [],
        "sections": [
            _summary_table_section(
                title=section.replace("_", " ").title(),
                rows=data.get("rows", []),
            )
        ],
    }


def _summary_overview(
    data: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = [
        ("Documents", data.get("documents")),
        (
            "Documents with annotations",
            data.get("documents_with_annotations"),
        ),
        (
            "Documents without annotations",
            data.get("documents_without_annotations"),
        ),
        ("Annotations", data.get("annotations")),
        (
            "Annotations per document",
            data.get("annotations_per_document"),
        ),
    ]

    return [
        {
            "label": label,
            "value": value,
        }
        for label, value in rows
        if value is not None
    ]


def _summary_table_section(
    *,
    title: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "title": title,
        "fields": _fieldnames_from_rows(rows),
        "rows": rows,
    }


def _fieldnames_from_rows(
    rows: list[dict[str, Any]],
) -> list[str]:
    fields: list[str] = []

    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)

    return fields


def _looks_like_summary(
    data: dict[str, Any],
) -> bool:
    return any(
        key in data
        for key in [
            "by_layer",
            "by_label",
            "by_layer_label",
            "top_annotations",
        ]
    )