import typer

from umuannotator.cli import ontology
from umuannotator.renderers.json import corpus_to_dict

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
    text: list[str] = typer.Option(..., "--text", "-t"),
    annotator: list[str] = typer.Option(
        [],
        "--annotator",
        "-a",
        help="Annotator to enable. Can be used multiple times.",
    ),
    ontology_path: str | None = typer.Option(None, "--ontology", "-o"),
    language: str = typer.Option("es", "--language", "-l"),
    use_tfidf: bool = typer.Option(
        False,
        "--tfidf",
        help="Calculate TF-IDF scores after annotation.",
    ),
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
    documents = pipeline.run_texts(text)

    if use_tfidf:
        from umuannotator.metrics import TfidfScorer

        documents = TfidfScorer(layer="ontology").score(documents)

    print_json(
        data=corpus_to_dict(documents)
    )