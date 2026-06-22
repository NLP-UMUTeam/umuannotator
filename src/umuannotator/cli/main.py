import typer

from umuannotator.cli import ontology

app = typer.Typer(
    help="UMU Annotator: modular annotation toolkit."
)

app.add_typer(
    ontology.app,
    name="ontology",
    help="Ontology-related commands.",
)


@app.command()
def annotate(
    text: str = typer.Option(..., "--text", "-t"),
    annotator: list[str] = typer.Option(
        [],
        "--annotator",
        "-a",
        help="Annotator to enable. Can be used multiple times.",
    ),
    ontology_path: str | None = typer.Option(None, "--ontology", "-o"),
    language: str = typer.Option("es", "--language", "-l"),
):
    from rich import print_json

    from umuannotator.annotators.registry import build_annotators
    from umuannotator.pipeline import AnnotationPipeline

    annotators = build_annotators(
        annotator,
        language=language,
        ontology_path=ontology_path,
    )

    pipeline = AnnotationPipeline(annotators)
    document = pipeline.run_text(text)

    print_json(data={
        "text": document.text,
        "annotations": [
            annotation.__dict__
            for annotation in document.annotations
        ],
    })