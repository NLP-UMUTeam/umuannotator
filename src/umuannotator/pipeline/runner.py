from __future__ import annotations

from umuannotator.io.loader import load_corpus_input
from umuannotator.annotators.registry import build_annotators
from umuannotator.config.loader import load_config
from umuannotator.metrics import ExtendedTfidfScorer, TfidfScorer
from umuannotator.ontology.graph import build_graph
from umuannotator.ontology.loader import load_ontology
from umuannotator.pipeline import AnnotationPipeline
from umuannotator.preprocessors.registry import build_preprocessors
from umuannotator.renderers.colors import collect_layer_colors
from umuannotator.renderers.json import corpus_to_dict
from umuannotator.resolution.resolver import (
    apply_resolver_if_enabled,
    resolver_config_from_dict,
)
from umuannotator.utils.profiling import timed


def run_from_config(
    *,
    config_path: str,
    input_path: str,
    input_format: str | None = None,
    text_column: str = "text",
    id_column: str = "id",
    sep: str = ",",
    show_progress: bool = True,
) -> dict:
    timings = {}

    with timed("load_config", timings):
        config = load_config(config_path)

    ontology_config = config.get("ontology", {})
    ontology_path = ontology_config.get("path")
    language = ontology_config.get("language", "es")

    with timed("build_preprocessors", timings):
        preprocessors = build_preprocessors(
            config.get("preprocessors", []),
            language=language,
        )

    with timed("build_annotators", timings):
        annotators = build_annotators(
            config.get("annotators", []),
            language=language,
            ontology_path=ontology_path,
            config=config,
        )

    with timed("load_input", timings):
        corpus = load_corpus_input(
            input_path,
            input_format=input_format,
            text_column=text_column,
            id_column=id_column,
            sep=sep,
        )

    pipeline = AnnotationPipeline(
        annotators=annotators,
        preprocessors=preprocessors,
    )

    with timed("annotation", timings):
        corpus = pipeline.run_corpus(
            corpus,
            show_progress=show_progress,
        )

    resolver_config = resolver_config_from_dict(
        config.get("resolver"),
    )

    if resolver_config.enabled:
        with timed("resolver", timings):
            for document in corpus.documents:
                document.annotations = apply_resolver_if_enabled(
                    document.annotations,
                    config=resolver_config,
                )

    metrics_config = config.get("metrics", {})

    corpus = _run_tfidf(
        corpus=corpus,
        metrics_config=metrics_config,
        timings=timings,
    )

    corpus = _run_extended_tfidf(
        corpus=corpus,
        metrics_config=metrics_config,
        ontology_path=ontology_path,
        config=config,
        timings=timings,
    )

    with timed("serialization", timings):
        data = corpus_to_dict(corpus)

    data["metadata"] = {
        "layer_colors": collect_layer_colors(config),
        "timings": timings,
        "annotator_timings": pipeline.timings,
        "documents": len(corpus.documents),
        "annotations": sum(
            len(document.annotations)
            for document in corpus.documents
        ),
        "preprocessors": [
            type(preprocessor).__name__
            for preprocessor in preprocessors
        ],
    }

    return data


def _run_tfidf(
    *,
    corpus,
    metrics_config: dict,
    timings: dict[str, float],
):
    tfidf_config = metrics_config.get("tfidf", {})

    if not tfidf_config.get("enabled", False):
        return corpus

    with timed("tfidf", timings):
        return TfidfScorer(
            layer=tfidf_config.get("layer", "ontology"),
        ).score(corpus)


def _run_extended_tfidf(
    *,
    corpus,
    metrics_config: dict,
    ontology_path: str | None,
    config: dict,
    timings: dict[str, float],
):
    extended_config = metrics_config.get("extended_tfidf", {})

    if not extended_config.get("enabled", False):
        return corpus

    if ontology_path is None:
        raise ValueError("extended_tfidf requires ontology.path")

    with timed("extended_tfidf", timings):
        rdf_graph = load_ontology(ontology_path)

        ontology_graph = build_graph(
            rdf_graph,
            config,
        )

        decay_config = extended_config.get("decay", {})

        return ExtendedTfidfScorer(
            ontology_graph=ontology_graph,
            decay=decay_config.get("value", 0.5),
            decay_function=decay_config.get("type", "exponential"),
            max_distance=extended_config.get("max_distance", 5),
            layer=extended_config.get("layer", "ontology"),
        ).score(corpus)