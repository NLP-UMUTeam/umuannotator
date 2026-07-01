from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from umuannotator.io.render import read_render_input
from umuannotator.metrics.summary import summarize_annotations
from umuannotator.metrics.salience import compute_salience
from umuannotator.metrics.output import write_metrics_json
from umuannotator.metrics.extended_salience import compute_extended_salience
from umuannotator.metrics.ontology_expansion import graph_to_distance_map
from umuannotator.metrics.ontology_expansion import (
    graph_to_distance_map,
    rdf_to_expansion_graph,
)
from umuannotator.ontology.loader import load_ontology


app = typer.Typer(help="Metric and corpus summary commands.")
console = Console()


@app.command("summary")
def summary(
    input_path: str = typer.Option(..., "--input", "-i"),
    input_format: str | None = typer.Option(
        None,
        "--input-format",
        help="Input format: json or jsonl. Required when --input -.",
    ),
    top: int = typer.Option(
        20,
        "--top",
        help="Number of top rows to show per section.",
    ),
    output_path: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path. Defaults to console.",
    ),
    output_format: str = typer.Option(
        "console",
        "--output-format",
        help="Output format: console or json.",
    ),    
):
    data = read_render_input(
        input_path,
        input_format=input_format,
    )

    summary_data = summarize_annotations(
        data,
        top=top,
    )

    if output_format == "console":
        render_summary(summary_data)
        return

    if output_format == "json":
        write_metrics_json(
            summary_data,
            output_path,
        )
        return

    raise ValueError(f"Unsupported output format: {output_format}")


def render_summary(summary_data: dict) -> None:
    console.print()
    console.print("[bold]Corpus summary[/bold]")
    console.print()

    overview = Table(show_header=False)
    overview.add_column("Metric", style="bold")
    overview.add_column("Value", justify="right")

    overview.add_row("Documents", str(summary_data["documents"]))
    overview.add_row(
        "Documents with annotations",
        str(summary_data["documents_with_annotations"]),
    )
    overview.add_row(
        "Documents without annotations",
        str(summary_data["documents_without_annotations"]),
    )
    overview.add_row("Annotations", str(summary_data["annotations"]))
    overview.add_row(
        "Annotations per document",
        f"{summary_data['annotations_per_document']:.2f}",
    )

    console.print(overview)

    _print_counter_table(
        title="By layer",
        rows=summary_data["by_layer"],
        key_name="Layer",
    )

    _print_counter_table(
        title="By label",
        rows=summary_data["by_label"],
        key_name="Label",
    )

    _print_layer_label_table(
        title="By layer / label",
        rows=summary_data["by_layer_label"],
    )

    _print_annotation_table(
        title="Top annotations",
        rows=summary_data["top_annotations"],
    )


def _print_counter_table(
    *,
    title: str,
    rows: list[dict],
    key_name: str,
) -> None:
    console.print()
    table = Table(title=title)
    table.add_column(key_name)
    table.add_column("Count", justify="right")

    for row in rows:
        table.add_row(
            str(row["key"]),
            str(row["count"]),
        )

    console.print(table)


def _print_layer_label_table(
    *,
    title: str,
    rows: list[dict],
) -> None:
    console.print()
    table = Table(title=title)
    table.add_column("Layer")
    table.add_column("Label")
    table.add_column("Count", justify="right")

    for row in rows:
        table.add_row(
            str(row["layer"]),
            str(row["label"]),
            str(row["count"]),
        )

    console.print(table)


def _print_annotation_table(
    *,
    title: str,
    rows: list[dict],
) -> None:
    console.print()
    table = Table(title=title)
    table.add_column("Text")
    table.add_column("Layer")
    table.add_column("Label")
    table.add_column("Count", justify="right")

    for row in rows:
        table.add_row(
            str(row["text"]),
            str(row["layer"]),
            str(row["label"]),
            str(row["count"]),
        )

    console.print(table)


@app.command("salience")
def salience(
    input_path: str = typer.Option(..., "--input", "-i"),
    input_format: str | None = typer.Option(
        None,
        "--input-format",
        help="Input format: json or jsonl. Required when --input -.",
    ),
    top: int = typer.Option(
        20,
        "--top",
        help="Number of top rows to show.",
    ),
    layer: str | None = typer.Option(
        None,
        "--layer",
        help="Only include annotations from this layer.",
    ),
    label: str | None = typer.Option(
        None,
        "--label",
        help="Only include annotations with this label.",
    ),
    output_path: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path. Defaults to console.",
    ),
    output_format: str = typer.Option(
        "console",
        "--output-format",
        help="Output format: console or json.",
    ),
    method: str = typer.Option(
        "tfidf",
        "--method",
        help="Salience method: tfidf or tfidf-e.",
    ),
    ontology_path: str | None = typer.Option(
        None,
        "--ontology",
        help="Ontology path. Required for --method tfidf-e.",
    ),
    max_distance: int = typer.Option(
        2,
        "--max-distance",
        help="Maximum ontology graph distance for tfidf-e.",
    ),
    decay: float = typer.Option(
        0.5,
        "--decay",
        help="Decay factor for tfidf-e expansion.",
    ),
    direction: str = typer.Option(
        "outgoing",
        "--direction",
        help="Ontology expansion direction for tfidf-e: outgoing, incoming or both.",
    ),   
    explain: str | None = typer.Option(
        None,
        "--explain",
        help="Explain one concept in TF-IDF-e output by full URI or short name.",
    ),    
):
    
    if explain is not None and method != "tfidf-e":
        raise ValueError("--explain is only supported with --method tfidf-e")

    data = read_render_input(
        input_path,
        input_format=input_format,
    )

    if method == "tfidf":
        salience_data = compute_salience(
            data,
            top=top,
            layer=layer,
            label=label,
        )

    elif method == "tfidf-e":
        if ontology_path is None:
            raise ValueError("--ontology is required when --method tfidf-e")

        if label is not None:
            raise ValueError("--label is not supported with --method tfidf-e yet")

        rdf_graph = load_ontology(ontology_path)

        expansion_graph = rdf_to_expansion_graph(
            rdf_graph,
            include_subclass=True,
            include_type=True,
        )

        distance_map = graph_to_distance_map(
            expansion_graph,
            max_distance=max_distance,
            direction=direction,
        )

        salience_data = compute_extended_salience(
            data,
            ontology_graph=distance_map,
            top=top,
            layer=layer or "ontology",
            max_distance=max_distance,
            decay=decay,
            direction=direction,
        )

    if output_format == "console":
        if explain is not None:
            render_salience_explanation(
                salience_data,
                explain,
            )
            return
        render_salience(salience_data)
        return
    
    if output_format == "json":
        if explain is not None:
            write_metrics_json(
                explain_salience_item(
                    salience_data,
                    explain,
                ),
                output_path,
            )
            return

        write_metrics_json(
            salience_data,
            output_path,
        )
        return    

    raise ValueError(f"Unsupported output format: {output_format}")


def render_salience(salience_data: dict) -> None:
    console.print()
    console.print("[bold]Annotation salience[/bold]")
    console.print()

    method = salience_data.get("method", "tfidf")

    console.print(f"Documents: {salience_data['documents']}")
    console.print(f"Method: {method}")

    if method == "tfidf-e":
        console.print(f"Layer: {salience_data.get('layer', '')}")
        console.print(f"Max distance: {salience_data.get('max_distance', '')}")
        console.print(f"Decay: {salience_data.get('decay', '')}")
        console.print(f"Direction: {salience_data.get('direction', '')}")

    console.print()

    if method == "tfidf-e":
        _render_extended_salience_table(salience_data)
        return

    _render_basic_salience_table(salience_data)


def _render_basic_salience_table(salience_data: dict) -> None:
    table = Table(title="Top salient annotations")
    table.add_column("Score", justify="right")
    table.add_column("TF", justify="right")
    table.add_column("DF", justify="right")
    table.add_column("IDF", justify="right")
    table.add_column("Layer")
    table.add_column("Label")
    table.add_column("Display")
    table.add_column("Canonical")

    for item in salience_data["items"]:
        table.add_row(
            _format_float(item.get("score")),
            str(item.get("tf", "")),
            str(item.get("df", "")),
            _format_float(item.get("idf")),
            str(item.get("layer", "")),
            str(item.get("label", "")),
            str(item.get("display", "")),
            _shorten_uri(str(item.get("canonical", ""))),
        )

    console.print(table)


def _render_extended_salience_table(salience_data: dict) -> None:
    table = Table(title="Top TF-IDF-e concepts")
    table.add_column("Score", justify="right")
    table.add_column("Observed", justify="right")
    table.add_column("Expanded", justify="right")
    table.add_column("Exp%", justify="right")
    table.add_column("TF", justify="right")
    table.add_column("DF", justify="right")
    table.add_column("IDF", justify="right")
    table.add_column("Label")
    table.add_column("Display")
    table.add_column("Concept")

    for item in salience_data["items"]:
        score = float(item.get("score", 0.0) or 0.0)
        expanded_score = float(item.get("expanded_score", 0.0) or 0.0)

        table.add_row(
            _format_float(score),
            _format_float(item.get("observed_score")),
            _format_float(expanded_score),
            _format_percent(
                expanded_score,
                score,
            ),
            str(item.get("tf", "")),
            str(item.get("df", "")),
            _format_float(item.get("idf")),
            str(item.get("label", "")),
            str(item.get("display", "")),
            _shorten_uri(str(item.get("concept_uri", ""))),
        )

    console.print(table)


def _format_float(
    value,
    *,
    digits: int = 3,
) -> str:
    if value is None:
        return ""

    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _format_percent(
    part: float,
    total: float,
) -> str:
    if total <= 0:
        return "0.0%"

    return f"{(part / total) * 100:.1f}%"


def _shorten_uri(value: str) -> str:
    if not value:
        return ""

    if "#" in value:
        return value.rsplit("#", 1)[-1]

    if "/" in value:
        return value.rstrip("/").rsplit("/", 1)[-1]

    if value.startswith("concept_uri:"):
        return _shorten_uri(
            value.removeprefix("concept_uri:"),
        )

    return value


def explain_salience_item(
    salience_data: dict,
    target: str,
) -> dict:
    item = find_salience_item(
        salience_data,
        target,
    )

    return {
        "documents": salience_data.get("documents", 0),
        "method": salience_data.get("method", ""),
        "layer": salience_data.get("layer", ""),
        "max_distance": salience_data.get("max_distance"),
        "decay": salience_data.get("decay"),
        "direction": salience_data.get("direction"),
        "item": item,
    }


def find_salience_item(
    salience_data: dict,
    target: str,
) -> dict:
    normalized_target = _normalize_explain_target(target)

    for item in salience_data.get("items", []):
        if _matches_explain_target(
            item,
            normalized_target,
        ):
            return item

    raise ValueError(f"Concept not found in salience results: {target}")


def render_salience_explanation(
    salience_data: dict,
    target: str,
) -> None:
    explanation = explain_salience_item(
        salience_data,
        target,
    )

    item = explanation["item"]

    console.print()
    console.print("[bold]TF-IDF-e explanation[/bold]")
    console.print()

    console.print(f"Documents: {explanation['documents']}")
    console.print(f"Layer: {explanation.get('layer', '')}")
    console.print(f"Max distance: {explanation.get('max_distance', '')}")
    console.print(f"Decay: {explanation.get('decay', '')}")
    console.print(f"Direction: {explanation.get('direction', '')}")
    console.print()

    overview = Table(show_header=False)
    overview.add_column("Metric", style="bold")
    overview.add_column("Value", justify="right")

    score = float(item.get("score", 0.0) or 0.0)
    observed_score = float(item.get("observed_score", 0.0) or 0.0)
    expanded_score = float(item.get("expanded_score", 0.0) or 0.0)

    overview.add_row(
        "Concept",
        _shorten_uri(str(item.get("concept_uri", ""))),
    )
    overview.add_row(
        "Display",
        str(item.get("display", "")),
    )
    overview.add_row(
        "Label",
        str(item.get("label", "")),
    )
    overview.add_row(
        "Score",
        _format_float(score),
    )
    overview.add_row(
        "Observed",
        _format_float(observed_score),
    )
    overview.add_row(
        "Expanded",
        _format_float(expanded_score),
    )
    overview.add_row(
        "Expanded %",
        _format_percent(
            expanded_score,
            score,
        ),
    )
    overview.add_row(
        "TF",
        str(item.get("tf", "")),
    )
    overview.add_row(
        "DF",
        str(item.get("df", "")),
    )
    overview.add_row(
        "IDF",
        _format_float(item.get("idf")),
    )

    console.print(overview)

    _render_expanded_from_table(
        item.get("expanded_from", []),
    )


def _render_expanded_from_table(
    expanded_from: list[dict],
) -> None:
    if not expanded_from:
        console.print()
        console.print("[dim]No expanded contributions.[/dim]")
        return

    table = Table(title="Expanded from")
    table.add_column("Source")
    table.add_column("Distance", justify="right")
    table.add_column("Contribution", justify="right")

    for contribution in expanded_from:
        table.add_row(
            _shorten_uri(str(contribution.get("source", ""))),
            str(contribution.get("distance", "")),
            _format_float(contribution.get("contribution")),
        )

    console.print()
    console.print(table)


def _matches_explain_target(
    item: dict,
    normalized_target: str,
) -> bool:
    concept_uri = str(item.get("concept_uri", ""))
    canonical = str(item.get("canonical", ""))
    short_concept = _shorten_uri(concept_uri)
    short_canonical = _shorten_uri(canonical)

    candidates = {
        _normalize_explain_target(concept_uri),
        _normalize_explain_target(canonical),
        _normalize_explain_target(short_concept),
        _normalize_explain_target(short_canonical),
    }

    return normalized_target in candidates


def _normalize_explain_target(
    value: str,
) -> str:
    value = value.strip()

    if value.startswith("concept_uri:"):
        value = value.removeprefix("concept_uri:")

    return value