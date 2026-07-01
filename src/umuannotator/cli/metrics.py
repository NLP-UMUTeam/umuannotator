from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from umuannotator.io.render import read_render_input
from umuannotator.metrics.summary import summarize_annotations
from umuannotator.metrics.salience import compute_salience
from umuannotator.metrics.output import write_metrics_json


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
):
    data = read_render_input(
        input_path,
        input_format=input_format,
    )

    salience_data = compute_salience(
        data,
        top=top,
        layer=layer,
        label=label,
    )

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
            f"{item['score']:.3f}",
            str(item["tf"]),
            str(item["df"]),
            f"{item['idf']:.3f}",
            str(item["layer"]),
            str(item["label"]),
            str(item["display"]),
            str(item["canonical"]),
        )

    console.print(table)