from __future__ import annotations

from pathlib import Path
from copy import deepcopy
import json

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
    session_metadata: dict = {}

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

        if text == ":meta":
            if session_metadata:
                console.print_json(data=session_metadata)
            else:
                console.print("[dim]No session metadata set.[/dim]")
            continue

        if text == ":meta clear":
            session_metadata.clear()
            console.print("[green]Metadata cleared.[/green]")
            continue

        if text.startswith(":meta unset "):
            key = text[len(":meta unset "):].strip()

            if not key:
                console.print(
                    "[yellow]Usage: :meta unset <key>[/yellow]"
                )
                continue

            removed = _unset_nested_metadata(
                session_metadata,
                key,
            )

            if removed:
                console.print(
                    f"[green]Metadata {key} removed.[/green]"
                )
            else:
                console.print(
                    f"[yellow]Metadata {key} not found.[/yellow]"
                )

            continue

        if text.startswith(":meta "):
            payload = text[len(":meta "):].strip()

            parts = payload.split(maxsplit=1)

            if len(parts) != 2:
                console.print(
                    "[yellow]Usage: :meta <key> <value>[/yellow]"
                )
                continue

            key, raw_value = parts

            value = _parse_metadata_value(raw_value)

            try:
                _set_nested_metadata(
                    session_metadata,
                    key,
                    value,
                )
            except ValueError as exc:
                console.print(
                    f"[red]{exc}[/red]"
                )
                continue

            console.print(
                f"[green]Metadata {key} set.[/green]"
            )
            continue

        document = _annotate_text(
            text,
            pipeline=pipeline,
            pipeline_context=pipeline_context,
            metadata=session_metadata,
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
        "[cyan]:table[/cyan], "
        "[cyan]:meta[/cyan], "
        "[cyan]:meta <key> <value>[/cyan], "
        "[cyan]:meta unset <key>[/cyan], "
        "[cyan]:meta clear[/cyan]"
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
    metadata: dict | None = None,
) -> Document:
    document = Document(
        text=text,
        metadata=deepcopy(metadata or {}),
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


def _parse_metadata_value(
    value: str,
):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _set_nested_metadata(
    metadata: dict,
    key: str,
    value,
) -> None:
    parts = key.split(".")
    current = metadata

    for part in parts[:-1]:
        existing = current.get(part)

        if existing is None:
            current[part] = {}
            current = current[part]
            continue

        if not isinstance(existing, dict):
            raise ValueError(
                f"Cannot set nested metadata '{key}': "
                f"'{part}' is not an object."
            )

        current = existing

    current[parts[-1]] = value


def _unset_nested_metadata(
    metadata: dict,
    key: str,
) -> bool:
    parts = key.split(".")
    current = metadata

    parents = []

    for part in parts[:-1]:
        value = current.get(part)

        if not isinstance(value, dict):
            return False

        parents.append((current, part))
        current = value

    leaf = parts[-1]

    if leaf not in current:
        return False

    del current[leaf]

    # Remove empty parent dictionaries.
    for parent, part in reversed(parents):
        child = parent.get(part)

        if isinstance(child, dict) and not child:
            del parent[part]
        else:
            break

    return True


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