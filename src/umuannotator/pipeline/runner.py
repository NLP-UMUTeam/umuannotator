from __future__ import annotations

from time import perf_counter

from math import ceil
from time import perf_counter

from tqdm.auto import tqdm

from umuannotator.annotation_enrichers.registry import (
    build_annotation_enrichers,
)
from umuannotator.annotators.registry import build_annotators
from umuannotator.config.loader import load_config
from umuannotator.io.loader import (
    count_corpus_input_documents,
    iter_corpus_input_batches,
    load_corpus_input,
)
from umuannotator.io.output import (
    infer_output_format,
    write_output,
)
from umuannotator.metrics import (
    ExtendedTfidfScorer,
    TfidfScorer,
)
from umuannotator.ontology.graph import build_graph
from umuannotator.ontology.loader import load_ontology
from umuannotator.pipeline import (
    AnnotationEnrichmentPipeline,
    AnnotationPipeline,
    RelationEnrichmentPipeline,
    RelationExtractionPipeline,
)
from umuannotator.preprocessors.registry import (
    build_preprocessors,
)
from umuannotator.relation_enrichers.registry import (
    build_relation_enrichers,
)
from umuannotator.relation_extractors.registry import (
    build_relation_extractors,
)
from umuannotator.renderers.json import corpus_to_dict


BATCH_SIZE = 100


def run_from_config(
    *,
    config_path: str,
    input_path: str,
    output_path: str,
    input_format: str | None = None,
    output_format: str | None = None,
    output_profile: str = "compact",
    text_column: str = "text",
    id_column: str = "id",
    sep: str = ",",
    show_progress: bool = True,
) -> dict:
    config = load_config(
        config_path
    )

    pipeline, pipeline_context = (
        build_pipeline_from_config(
            config
        )
    )

    resolved_output_format = (
        infer_output_format(
            output_path,
            output_format,
        )
    )

    if resolved_output_format == "jsonl":
        return _run_batched_jsonl(
            config=config,
            pipeline=pipeline,
            pipeline_context=pipeline_context,
            input_path=input_path,
            output_path=output_path,
            input_format=input_format,
            output_profile=output_profile,
            text_column=text_column,
            id_column=id_column,
            sep=sep,
            show_progress=show_progress,
        )

    return _run_full_corpus(
        config=config,
        pipeline=pipeline,
        pipeline_context=pipeline_context,
        input_path=input_path,
        output_path=output_path,
        input_format=input_format,
        output_format=resolved_output_format,
        output_profile=output_profile,
        text_column=text_column,
        id_column=id_column,
        sep=sep,
        show_progress=show_progress,
    )


def _run_batched_jsonl(
    *,
    config: dict,
    pipeline,
    pipeline_context: dict,
    input_path: str,
    output_path: str,
    input_format: str | None,
    output_profile: str,
    text_column: str,
    id_column: str,
    sep: str,
    show_progress: bool,
) -> dict:
    _ensure_no_corpus_metrics(
        config
    )

    # Truncate/create the output before processing.
    # This also creates parent directories.
    write_output(
        {
            "documents": [],
            "metadata": {},
        },
        output_path,
        output_format="jsonl",
        output_profile=output_profile,
        append=False,
    )

    total_documents = 0
    total_annotations = 0
    total_relations = 0
    total_batches = 0

    started = perf_counter()

    input_documents = count_corpus_input_documents(
        input_path,
        input_format=input_format,
        text_column=text_column,
        id_column=id_column,
        sep=sep,
    )

    expected_batches = (
        ceil(
            input_documents / BATCH_SIZE
        )
        if input_documents is not None
        else None
    )

    batches = iter_corpus_input_batches(
        input_path,
        input_format=input_format,
        text_column=text_column,
        id_column=id_column,
        sep=sep,
        batch_size=BATCH_SIZE,
    )

    with tqdm(
        total=expected_batches,
        desc="Processing",
        unit="batch",
        disable=not show_progress,
        dynamic_ncols=True,
    ) as progress:
        for corpus in batches:
            batch_documents = len(
                corpus.documents
            )

            corpus = _process_local_corpus(
                corpus=corpus,
                pipeline=pipeline,
                pipeline_context=(
                    pipeline_context
                ),
                show_progress=False,
            )

            data = corpus_to_dict(
                corpus
            )

            write_output(
                data,
                output_path,
                output_format="jsonl",
                output_profile=output_profile,
                append=True,
            )

            total_batches += 1
            total_documents += (
                batch_documents
            )

            total_annotations += sum(
                len(document.annotations)
                for document in corpus.documents
            )

            total_relations += sum(
                len(document.relations)
                for document in corpus.documents
            )

            progress.update(1)

    elapsed = (
        perf_counter() - started
    )

    return {
        "documents": total_documents,
        "annotations": total_annotations,
        "relations": total_relations,
        "batches": total_batches,
        "batch_size": BATCH_SIZE,
        "elapsed_seconds": elapsed,
    }


def _run_full_corpus(
    *,
    config: dict,
    pipeline,
    pipeline_context: dict,
    input_path: str,
    output_path: str,
    input_format: str | None,
    output_format: str,
    output_profile: str,
    text_column: str,
    id_column: str,
    sep: str,
    show_progress: bool,
) -> dict:
    corpus = load_corpus_input(
        input_path,
        input_format=input_format,
        text_column=text_column,
        id_column=id_column,
        sep=sep,
    )

    corpus = _process_local_corpus(
        corpus=corpus,
        pipeline=pipeline,
        pipeline_context=pipeline_context,
        show_progress=show_progress,
    )

    metrics_config = config.get(
        "metrics",
        {},
    )

    corpus = _run_tfidf(
        corpus=corpus,
        metrics_config=metrics_config,
    )

    corpus = _run_extended_tfidf(
        corpus=corpus,
        metrics_config=metrics_config,
        ontology_path=pipeline_context[
            "ontology_path"
        ],
        config=config,
    )

    data = corpus_to_dict(
        corpus
    )

    write_output(
        data,
        output_path,
        output_format=output_format,
        output_profile=output_profile,
    )

    return {
        "documents": len(
            corpus.documents
        ),
        "annotations": sum(
            len(document.annotations)
            for document in corpus.documents
        ),
        "relations": sum(
            len(document.relations)
            for document in corpus.documents
        ),
        "batches": 1,
        "batch_size": None,
    }


def _process_local_corpus(
    *,
    corpus,
    pipeline,
    pipeline_context: dict,
    show_progress: bool,
):
    annotation_enrichers = (
        pipeline_context[
            "annotation_enrichers"
        ]
    )

    annotation_enrichment_pipeline = (
        pipeline_context[
            "annotation_enrichment_pipeline"
        ]
    )

    relation_extractors = (
        pipeline_context[
            "relation_extractors"
        ]
    )

    relation_pipeline = (
        pipeline_context[
            "relation_pipeline"
        ]
    )

    relation_enrichers = (
        pipeline_context[
            "relation_enrichers"
        ]
    )

    relation_enrichment_pipeline = (
        pipeline_context[
            "relation_enrichment_pipeline"
        ]
    )

    corpus = pipeline.run_corpus(
        corpus,
        show_progress=show_progress,
    )

    if annotation_enrichers:
        corpus = (
            annotation_enrichment_pipeline
            .run_corpus(
                corpus,
                show_progress=show_progress,
            )
        )

    if relation_extractors:
        corpus = (
            relation_pipeline.run_corpus(
                corpus,
                show_progress=show_progress,
            )
        )

    if relation_enrichers:
        corpus = (
            relation_enrichment_pipeline
            .run_corpus(
                corpus,
                show_progress=show_progress,
            )
        )

    return corpus


def _ensure_no_corpus_metrics(
    config: dict,
) -> None:
    metrics_config = config.get(
        "metrics",
        {},
    )

    tfidf_enabled = (
        metrics_config.get(
            "tfidf",
            {},
        ).get(
            "enabled",
            False,
        )
    )

    extended_enabled = (
        metrics_config.get(
            "extended_tfidf",
            {},
        ).get(
            "enabled",
            False,
        )
    )

    if (
        tfidf_enabled
        or extended_enabled
    ):
        raise NotImplementedError(
            "Corpus-level metrics cannot yet "
            "be used with batched JSONL output. "
            "They will be handled in a global "
            "second pass."
        )


def build_pipeline_from_config(
    config: dict,
) -> tuple[AnnotationPipeline, dict]:
    ontology_config = config.get(
        "ontology",
        {},
    )

    ontology_path = ontology_config.get(
        "path"
    )

    language = ontology_config.get(
        "language",
        "es",
    )

    preprocessors = build_preprocessors(
        config.get(
            "preprocessors",
            [],
        ),
        language=language,
    )

    annotators = build_annotators(
        config.get(
            "annotators",
            [],
        ),
        language=language,
        ontology_path=ontology_path,
        config=config,
    )

    pipeline = AnnotationPipeline(
        annotators=annotators,
        preprocessors=preprocessors,
    )

    annotation_enrichers = (
        build_annotation_enrichers(
            config.get(
                "annotation_enrichers",
                [],
            ),
        )
    )

    annotation_enrichment_pipeline = (
        AnnotationEnrichmentPipeline(
            enrichers=(
                annotation_enrichers
            ),
        )
    )

    relation_extractors = (
        build_relation_extractors(
            config.get(
                "relation_extractors",
                [],
            ),
            language=language,
        )
    )

    relation_pipeline = (
        RelationExtractionPipeline(
            extractors=(
                relation_extractors
            ),
        )
    )

    relation_enrichers = (
        build_relation_enrichers(
            config.get(
                "relation_enrichers",
                [],
            ),
            language=language,
        )
    )

    relation_enrichment_pipeline = (
        RelationEnrichmentPipeline(
            enrichers=(
                relation_enrichers
            ),
        )
    )

    return pipeline, {
        "preprocessors": preprocessors,
        "annotators": annotators,
        "relation_extractors": (
            relation_extractors
        ),
        "relation_pipeline": (
            relation_pipeline
        ),
        "relation_enrichers": (
            relation_enrichers
        ),
        "annotation_enrichers": (
            annotation_enrichers
        ),
        "annotation_enrichment_pipeline": (
            annotation_enrichment_pipeline
        ),
        "relation_enrichment_pipeline": (
            relation_enrichment_pipeline
        ),
        "language": language,
        "ontology_path": ontology_path,
    }


def _run_tfidf(
    *,
    corpus,
    metrics_config: dict,
):
    tfidf_config = metrics_config.get(
        "tfidf",
        {},
    )

    if not tfidf_config.get(
        "enabled",
        False,
    ):
        return corpus

    return TfidfScorer(
        layer=tfidf_config.get(
            "layer",
            "ontology",
        ),
    ).score(
        corpus
    )


def _run_extended_tfidf(
    *,
    corpus,
    metrics_config: dict,
    ontology_path: str | None,
    config: dict,
):
    extended_config = (
        metrics_config.get(
            "extended_tfidf",
            {},
        )
    )

    if not extended_config.get(
        "enabled",
        False,
    ):
        return corpus

    if ontology_path is None:
        raise ValueError(
            "extended_tfidf requires "
            "ontology.path"
        )

    rdf_graph = load_ontology(
        ontology_path
    )

    ontology_graph = build_graph(
        rdf_graph,
        config,
    )

    decay_config = (
        extended_config.get(
            "decay",
            {},
        )
    )

    return ExtendedTfidfScorer(
        ontology_graph=ontology_graph,
        decay=decay_config.get(
            "value",
            0.5,
        ),
        decay_function=decay_config.get(
            "type",
            "exponential",
        ),
        max_distance=extended_config.get(
            "max_distance",
            5,
        ),
        layer=extended_config.get(
            "layer",
            "ontology",
        ),
    ).score(
        corpus
    )