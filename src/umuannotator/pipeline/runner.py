from __future__ import annotations

from umuannotator.io.loader import load_corpus_input
from umuannotator.annotators.registry import build_annotators
from umuannotator.config.loader import load_config
from umuannotator.metrics import ExtendedTfidfScorer, TfidfScorer
from umuannotator.ontology.graph import build_graph
from umuannotator.ontology.loader import load_ontology
from umuannotator.pipeline import (
    AnnotationPipeline,
    RelationExtractionPipeline,
)
from umuannotator.relation_extractors.registry import (
    build_relation_extractors,
)

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

    with timed("build_pipeline", timings):
        pipeline, pipeline_context = build_pipeline_from_config(config)

    preprocessors = pipeline_context["preprocessors"]
    ontology_path = pipeline_context["ontology_path"]
    relation_extractors = pipeline_context["relation_extractors"]
    relation_pipeline = pipeline_context["relation_pipeline"]

    with timed("load_input", timings):
        corpus = load_corpus_input(
            input_path,
            input_format=input_format,
            text_column=text_column,
            id_column=id_column,
            sep=sep,
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

    if relation_extractors:
        with timed("relation_extraction", timings):
            corpus = relation_pipeline.run_corpus(
                corpus,
                show_progress=show_progress,
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
        "relation_extractor_timings": (
            relation_pipeline.timings
        ),
        "documents": len(corpus.documents),
        "annotations": sum(
            len(document.annotations)
            for document in corpus.documents
        ),
        "relations": sum(
            len(document.relations)
            for document in corpus.documents
        ),
        "preprocessors": [
            type(preprocessor).__name__
            for preprocessor in preprocessors
        ],
        "relation_extractors": [
            type(extractor).__name__
            for extractor in relation_extractors
        ],
    }

    return data


def build_pipeline_from_config(
    config: dict,
) -> tuple[AnnotationPipeline, dict]:
    ontology_config = config.get("ontology", {})
    ontology_path = ontology_config.get("path")
    language = ontology_config.get("language", "es")

    preprocessors = build_preprocessors(
        config.get("preprocessors", []),
        language=language,
    )

    annotators = build_annotators(
        config.get("annotators", []),
        language=language,
        ontology_path=ontology_path,
        config=config,
    )

    pipeline = AnnotationPipeline(
        annotators=annotators,
        preprocessors=preprocessors,
    )

    relation_extractors = build_relation_extractors(
        config.get("relation_extractors", []),
        language=language,
    )

    relation_pipeline = RelationExtractionPipeline(
        extractors=relation_extractors,
    )

    return pipeline, {
        "preprocessors": preprocessors,
        "annotators": annotators,
        "relation_extractors": relation_extractors,
        "relation_pipeline": relation_pipeline,
        "language": language,
        "ontology_path": ontology_path,
    }


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