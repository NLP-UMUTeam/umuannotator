import typer

from umuannotator.cli import (
    metrics,
    ontology,
    preprocess,
    render,
    shell,
)
from umuannotator.pipeline.runner import (
    run_from_config,
)


app = typer.Typer(
    help=(
        "UMU Annotator: modular "
        "annotation toolkit."
    )
)

app.add_typer(
    metrics.app,
    name="metrics",
)
app.add_typer(
    ontology.app,
    name="ontology",
)
app.add_typer(
    preprocess.app,
    name="preprocess",
)
app.add_typer(
    render.app,
    name="render",
)
app.add_typer(
    shell.app,
    name="shell",
)


@app.command()
def run(
    config_path: str = typer.Option(
        ...,
        "--config",
        "-c",
    ),
    input_path: str = typer.Option(
        ...,
        "--input",
        "-i",
    ),
    output_path: str = typer.Option(
        ...,
        "--output",
        "-o",
    ),
    text_column: str = typer.Option(
        "text",
        "--text-column",
    ),
    input_format: str | None = typer.Option(
        None,
        "--input-format",
        help=(
            "Input format: csv, jsonl or "
            "text. Inferred from file "
            "extension when omitted."
        ),
    ),
    output_format: str | None = typer.Option(
        None,
        "--output-format",
        help=(
            "Output format: json, jsonl or "
            "text. Inferred from file "
            "extension when omitted."
        ),
    ),
    id_column: str = typer.Option(
        "id",
        "--id-column",
        help=(
            "Document id column for "
            "structured inputs."
        ),
    ),
    sep: str = typer.Option(
        ",",
        "--sep",
    ),
    show_progress: bool = typer.Option(
        True,
        "--progress/--no-progress",
        help="Show progress bars.",
    ),
    output_profile: str = typer.Option(
        "compact",
        "--output-profile",
        help=(
            "Output profile: compact "
            "or full."
        ),
    ),
    batch_size: int = typer.Option(
        100,
        "--batch-size",
        min=1,
        help="Number of documents processed per batch.",
    ),    
    resume: bool = typer.Option(
        False,
        "--resume",
        help=(
            "Resume an interrupted batched "
            "JSONL run from its workspace."
        ),
    ),
):
    summary = run_from_config(
        config_path=config_path,
        input_path=input_path,
        output_path=output_path,
        input_format=input_format,
        output_format=output_format,
        output_profile=output_profile,
        text_column=text_column,
        id_column=id_column,
        sep=sep,
        show_progress=show_progress,
        batch_size=batch_size,
        resume=resume,
    )

    if summary.get(
        "already_completed",
        False,
    ):
        typer.echo(
            "The workspace is already completed."
        )
        return

    if summary.get(
        "resumed",
        False,
    ):
        typer.echo(
            "Resumed run."
        )
    else:
        typer.echo(
            (
                f"Processed "
                f"{summary['documents']:,} documents, "
                f"{summary['annotations']:,} annotations, "
                f"{summary['relations']:,} relations."
            )
        )

    stage1 = summary.get(
        "stage1"
    )

    if stage1 is not None:
        typer.echo(
            (
                f"Pass 1: "
                f"{stage1['processed_batches']:,} "
                f"batches processed, "
                f"{stage1['reused_batches']:,} reused."
            )
        )

    stage2 = summary.get(
        "stage2"
    )

    if stage2 is not None:
        typer.echo(
            (
                f"Pass 2: "
                f"{stage2['processed_batches']:,} "
                f"batches processed, "
                f"{stage2['reused_batches']:,} reused."
            )
        )