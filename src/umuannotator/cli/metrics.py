import typer
from rich import print_json
from umuannotator.document import AnnotationResolver

app = typer.Typer(help="Metric commands.")


@app.command("tfidf")
def tfidf(
    input_path: str = typer.Option(..., "--input", "-i"),
    output_path: str | None = typer.Option(None, "--output", "-o"),
    text_column: str = typer.Option("text", "--text-column"),
    sep: str = typer.Option(",", "--sep"),
    ontology_path: str = typer.Option(..., "--ontology"),
    language: str = typer.Option("es", "--language", "-l"),
    extended: bool = typer.Option(False, "--extended"),
):
    import json
    import pandas as pd

    from umuannotator.annotators.registry import build_annotators
    from umuannotator.io.dataframe import dataframe_to_corpus
    from umuannotator.metrics import TfidfScorer
    from umuannotator.pipeline import AnnotationPipeline
    from umuannotator.renderers.json import corpus_to_dict

    df = pd.read_csv(input_path, sep=sep)

    corpus = dataframe_to_corpus(
        df,
        text_column=text_column,
    )

    annotators = build_annotators(
        ["ontology"],
        ontology_path=ontology_path,
        language=language,
    )

    pipeline = AnnotationPipeline(annotators)
    corpus = pipeline.run_corpus(corpus)
    corpus = AnnotationResolver(layer="ontology").resolve_corpus(corpus)
    corpus = TfidfScorer(layer="ontology").score(corpus)

    if extended:

        from umuannotator.metrics import ExtendedTfidfScorer
        from umuannotator.ontology.loader import load_ontology
        from umuannotator.ontology.index import build_index
        from umuannotator.ontology.graph import build_graph

        graph = load_ontology(ontology_path)
        concepts = build_index(graph)
        ontology_graph = build_graph(concepts)

        corpus = ExtendedTfidfScorer(
            ontology_graph=ontology_graph,
            decay=0.5,
            max_distance=5,
            layer="ontology",
        ).score(corpus)

    data = corpus_to_dict(corpus)


    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        print_json(data=data)