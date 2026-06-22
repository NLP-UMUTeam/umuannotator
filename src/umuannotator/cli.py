import typer
from rich import print_json

from umuannotator.annotators.ontology import OntologyAnnotator
from umuannotator.ontology.loader import load_ontology
from umuannotator.ontology.index import build_index
from umuannotator.pipeline import AnnotationPipeline


app = typer.Typer()


@app.callback()
def main():
    """
    UMU Annotator
    """
    pass


@app.command("annotate")
def annotate(
    ontology: str = typer.Option(..., "--ontology", "-o"),
    text: str = typer.Option(..., "--text", "-t"),
    language: str = typer.Option("es", "--language", "-l"),
    
):
    graph = load_ontology(ontology)
    concepts = build_index(graph)

    pipeline = AnnotationPipeline([
        OntologyAnnotator(
            concepts=concepts,
            source=ontology,
        )
    ])

    document = pipeline.run_text(text)

    data = {
        "text": document.text,
        "annotations": [
            annotation.__dict__
            for annotation in document.annotations
        ],
    }

    print_json(data=data)


if __name__ == "__main__":
    app() 