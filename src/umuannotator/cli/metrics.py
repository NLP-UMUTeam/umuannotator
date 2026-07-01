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
):
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

    else:
        raise ValueError(f"Unsupported salience method: {method}")

    if output_format == "console":
        render_salience(salience_data)
        return

    if output_format == "json":
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
    console.print(f"Documents: {salience_data['documents']}")
    console.print()

    has_extended_scores = any(
        "observed_score" in item or "expanded_score" in item
        for item in salience_data["items"]
    )

    table = Table(title="Top salient annotations")
    table.add_column("Score", justify="right")

    if has_extended_scores:
        table.add_column("Observed", justify="right")
        table.add_column("Expanded", justify="right")

    table.add_column("TF", justify="right")
    table.add_column("DF", justify="right")
    table.add_column("IDF", justify="right")
    table.add_column("Layer")
    table.add_column("Label")
    table.add_column("Display")
    table.add_column("Canonical")

    for item in salience_data["items"]:
        row = [
            f"{item['score']:.3f}",
        ]

        if has_extended_scores:
            row.extend(
                [
                    f"{item.get('observed_score', 0.0):.3f}",
                    f"{item.get('expanded_score', 0.0):.3f}",
                ]
            )

        row.extend(
            [
                str(item.get("tf", "")),
                str(item.get("df", "")),
                f"{item.get('idf', 0.0):.3f}",
                str(item.get("layer", "")),
                str(item.get("label", "")),
                str(item.get("display", "")),
                str(item.get("canonical", "")),
            ]
        )

        table.add_row(*row)

    console.print(table)