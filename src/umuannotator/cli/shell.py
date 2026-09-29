from __future__ import annotations

from pathlib import Path

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from rich.console import Console

from umuannotator.config.loader import load_config
from umuannotator.document.model import Document
from umuannotator.pipeline.runner import build_pipeline_from_config
from umuannotator.renderers.tables import document_annotations_table
from umuannotator.serialization.documents import serialize_document


app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def shell(
    config_path: str = typer.Option(
        ...,
        "--config",
        "-c",
        help="YAML configuration file.",
    ),
    output_format: str = typer.Option(
        "table",
        "--output-format",
        "-f",
        help="Output format: table or json.",
    ),
    output_profile: str = typer.Option(
        "compact",
        "--output-profile",
        help="Serialization profile for JSON output: compact or full.",
    ),
) -> None:
    """Start an interactive shell to annotate one text at a time."""
    config = load_config(config_path)
    pipeline, pipeline_context = build_pipeline_from_config(config)

    current_output_format = output_format

    _print_banner(pipeline_context)

    session = PromptSession(
        history=FileHistory(
            str(Path.home() / ".umuannotator_shell_history")
        ),
    )

    while True:
        try:
            text = session.prompt(
                FormattedText(
                    [
                        ("ansicyan bold", "umuannotator> "),
                    ]
                )
            )
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        text = text.strip()

        if not text:
            continue

        if text in {":quit", ":exit", "quit", "exit"}:
            break

        if text == ":json":
            current_output_format = "json"
            console.print("[green]Output format set to json.[/green]")
            continue

        if text == ":table":
            current_output_format = "table"
            console.print("[green]Output format set to table.[/green]")
            continue

        document = _annotate_text(
            text,
            pipeline=pipeline,
            pipeline_context=pipeline_context,
        )

        _render_document(
            document,
            output_format=current_output_format,
            output_profile=output_profile,
        )


def _print_banner(
    pipeline_context: dict,
) -> None:
    console.print("[bold]UMUAnnotator shell[/bold]")
    console.print("Type text to annotate.")
    console.print(
        "Commands: "
        "[cyan]:quit[/cyan], "
        "[cyan]:exit[/cyan], "
        "[cyan]:json[/cyan], "
        "[cyan]:table[/cyan]"
    )

    preprocessors = pipeline_context.get("preprocessors", [])
    annotators = pipeline_context.get("annotators", [])
    annotation_enrichers = pipeline_context.get(
        "annotation_enrichers",
        [],
    )
    relation_extractors = pipeline_context.get(
        "relation_extractors",
        [],
    )
    relation_enrichers = pipeline_context.get(
        "relation_enrichers",
        [],
    )

    _print_components("Preprocessors", preprocessors)
    _print_components("Annotators", annotators)
    _print_components(
        "Annotation enrichers",
        annotation_enrichers,
    )
    _print_components(
        "Relation extractors",
        relation_extractors,
    )
    _print_components(
        "Relation enrichers",
        relation_enrichers,
    )

    console.print()


def _print_components(
    label: str,
    components: list,
) -> None:
    if components:
        console.print(
            f"[dim]{label}:[/dim] "
            + ", ".join(
                type(item).__name__
                for item in components
            )
        )
        return

    console.print(f"[dim]{label}: none[/dim]")


def _annotate_text(
    text: str,
    *,
    pipeline,
    pipeline_context: dict,
) -> Document:
    document = Document(
        text=text,
        metadata={},
    )

    document = pipeline.run_document(document)

    annotation_enrichers = pipeline_context.get(
        "annotation_enrichers",
        [],
    )
    annotation_enrichment_pipeline = pipeline_context[
        "annotation_enrichment_pipeline"
    ]

    if annotation_enrichers:
        document = annotation_enrichment_pipeline.run_document(
            document
        )

    relation_extractors = pipeline_context.get(
        "relation_extractors",
        [],
    )
    relation_pipeline = pipeline_context[
        "relation_pipeline"
    ]

    if relation_extractors:
        document = relation_pipeline.run_document(document)

    relation_enrichers = pipeline_context.get(
        "relation_enrichers",
        [],
    )
    relation_enrichment_pipeline = pipeline_context[
        "relation_enrichment_pipeline"
    ]

    if relation_enrichers:
        document = relation_enrichment_pipeline.run_document(
            document
        )

    return document


def _render_document(
    document: Document,
    *,
    output_format: str,
    output_profile: str,
) -> None:
    if output_format == "table":
        _render_document_table(document)
        return

    if output_format == "json":
        console.print_json(
            data=serialize_document(
                document,
                output_profile=output_profile,
            )
        )
        return

    raise ValueError(
        f"Unsupported shell output format: {output_format}"
    )


def _render_document_table(
    document: Document,
) -> None:
    if not document.annotations:
        console.print("[dim]No annotations.[/dim]")
        return

    console.print(document_annotations_table(document))