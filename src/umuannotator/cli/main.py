import typer

from umuannotator.cli import ontology, preprocess, render
from umuannotator.io.output import write_output
from umuannotator.pipeline.runner import run_from_config


app = typer.Typer(
    help="UMU Annotator: modular annotation toolkit."
)

app.add_typer(
    ontology.app,
    name="ontology",
    help="Ontology-related commands.",
)

app.add_typer(
    render.app,
    name="render",
    help="Render annotated results.",
)

app.add_typer(
    preprocess.app,
    name="preprocess",
    help="Preprocessing commands.",
)


@app.command()
def run(
    config_path: str = typer.Option(..., "--config", "-c"),
    input_path: str = typer.Option(..., "--input", "-i"),
    output_path: str = typer.Option(..., "--output", "-o"),
    text_column: str = typer.Option("text", "--text-column"),
    input_format: str | None = typer.Option(
        None,
        "--input-format",
        help="Input format: csv, jsonl or text. Inferred from file extension when omitted.",
    ),
    output_format: str | None = typer.Option(
        None,
        "--output-format",
        help="Output format: json, jsonl or text. Inferred from file extension when omitted.",
    ),
    id_column: str = typer.Option(
        "id",
        "--id-column",
        help="Document id column for structured inputs.",
    ),  
    sep: str = typer.Option(",", "--sep"),
    show_progress: bool = typer.Option(
        True,
        "--progress/--no-progress",
        help="Show progress bars.",
    ),
):

    data = run_from_config(
        config_path=config_path,
        input_path=input_path,
        input_format=input_format,
        text_column=text_column,
        id_column=id_column,
        sep=sep,
        show_progress=show_progress,
    )


    write_output(
        data,
        output_path,
        output_format=output_format,
    )