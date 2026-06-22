import typer

from umuannotator.cli import ontology
from umuannotator.cli import metrics
from umuannotator.renderers.json import corpus_to_dict

app = typer.Typer(
    help="UMU Annotator: modular annotation toolkit."
)

app.add_typer(
    ontology.app,
    name="ontology",
    help="Ontology-related commands.",
)

app.add_typer(
    metrics.app,
    name="metrics",
    help="Metric-related commands.",
)


@app.command()
def annotate(
    text: list[str] = typer.Option([], "--text", "-t"),
    input_path: str | None = typer.Option(None, "--input", "-i"),
    output_path: str | None = typer.Option(None, "--output", "-o"),
    text_column: str = typer.Option("text", "--text-column"),
    sep: str = typer.Option(",", "--sep"),
    annotator: list[str] = typer.Option([], "--annotator", "-a"),
    ontology_path: str | None = typer.Option(None, "--ontology"),
    language: str = typer.Option("es", "--language", "-l"),
    use_tfidf: bool = typer.Option(False, "--tfidf"),
):
    from rich import print_json
    from tqdm import tqdm

    from umuannotator.annotators.registry import build_annotators
    from umuannotator.document import Corpus, Document
    from umuannotator.pipeline import AnnotationPipeline
    from umuannotator.renderers.json import corpus_to_dict

    documents = []

    if input_path:
        import pandas as pd

        df = pd.read_csv(input_path, sep=sep)

        for idx, row in tqdm(
            df.iterrows(),
            total=len(df),
            desc="Loading documents",
        ):
            document = Document(text=str(row[text_column]))
            document.metadata["doc_id"] = idx
            documents.append(document)

    for item in text:
        documents.append(Document(text=item))

    if not documents:
        raise typer.BadParameter("Use --text or --input.")

    annotators = build_annotators(
        annotator,
        language=language,
        ontology_path=ontology_path,
    )

    corpus = Corpus(documents=documents)

    pipeline = AnnotationPipeline(annotators)

    corpus.documents = [
        pipeline.run_document(document)
        for document in tqdm(
            corpus.documents,
            desc="Annotating documents",
        )
    ]

    if use_tfidf:
        from umuannotator.metrics import TfidfScorer

        corpus = TfidfScorer(layer="ontology").score(corpus)

    data = corpus_to_dict(corpus)

    if output_path:
        import json

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        print_json(data=data)


@app.command()
def run(
    config_path: str = typer.Option(..., "--config", "-c"),
    input_path: str = typer.Option(..., "--input", "-i"),
    output_path: str = typer.Option(..., "--output", "-o"),
    text_column: str = typer.Option("text", "--text-column"),
    sep: str = typer.Option(",", "--sep"),
):
    import json
    import pandas as pd

    from umuannotator.config.loader import load_config
    from umuannotator.annotators.registry import build_annotators
    from umuannotator.document import AnnotationResolver
    from umuannotator.io.dataframe import dataframe_to_corpus
    from umuannotator.metrics import TfidfScorer, ExtendedTfidfScorer
    from umuannotator.ontology.loader import load_ontology
    from umuannotator.ontology.index import build_index
    from umuannotator.ontology.graph import build_graph
    from umuannotator.pipeline import AnnotationPipeline
    from umuannotator.renderers.json import corpus_to_dict

    config = load_config(config_path)

    ontology_config = config.get("ontology", {})
    ontology_path = ontology_config.get("path")
    language = ontology_config.get("language", "es")

    annotator_names = [
        item["name"] if isinstance(item, dict) else item
        for item in config.get("annotators", [])
    ]

    df = pd.read_csv(input_path, sep=sep)

    corpus = dataframe_to_corpus(
        df,
        text_column=text_column,
    )

    annotators = build_annotators(
        annotator_names,
        language=language,
        ontology_path=ontology_path,
    )

    pipeline = AnnotationPipeline(annotators)
    corpus = pipeline.run_corpus(corpus)

    resolver_config = config.get("resolver", {})
    if resolver_config.get("enabled", True):
        corpus = AnnotationResolver(layer="ontology").resolve_corpus(corpus)

    metrics_config = config.get("metrics", {})

    tfidf_config = metrics_config.get("tfidf", {})
    if tfidf_config.get("enabled", False):
        corpus = TfidfScorer(
            layer=tfidf_config.get("layer", "ontology"),
        ).score(corpus)

    extended_config = metrics_config.get("extended_tfidf", {})
    if extended_config.get("enabled", False):
        graph = load_ontology(ontology_path)
        concepts = build_index(graph)

        direction = extended_config.get("direction", "ancestors")
        directed = direction == "ancestors"

        ontology_graph = build_graph(
            concepts,
            directed=directed,
        )

        decay_config = extended_config.get("decay", {})

        corpus = ExtendedTfidfScorer(
            ontology_graph=ontology_graph,
            decay=decay_config.get("value", 0.5),
            decay_function=decay_config.get("type", "exponential"),
            max_distance=extended_config.get("max_distance", 5),
            layer=extended_config.get("layer", "ontology"),
        ).score(corpus)

    data = corpus_to_dict(corpus)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)