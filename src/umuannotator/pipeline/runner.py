from __future__ import annotations

import json

from time import perf_counter
from collections import Counter
from math import ceil
from time import perf_counter
from tqdm.auto import tqdm
from pathlib import Path

from umuannotator.metrics.streaming import (
    collect_tfidf_statistics,
)
from umuannotator.pipeline.workspace import (
    assemble_batches,
    initialize_workspace,
    list_completed_batches,
    read_state,
    write_batch_atomic,
    write_state,
)
from umuannotator.serialization.documents import (
    deserialize_document,
    serialize_document,
)

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


DEFAULT_BATCH_SIZE = 100


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
    batch_size: int = DEFAULT_BATCH_SIZE,
    resume: bool = False,
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
            batch_size=batch_size,
            resume=resume,
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
    batch_size: int,
    resume: bool = False,
) -> dict:
    if output_path == "-":
        raise ValueError(
            "Batched workspace execution requires "
            "a file output path."
        )

    started = perf_counter()

    metrics = _resolve_metrics_config(
        config
    )

    stage2_required = (
        metrics["stage2_required"]
        or output_profile != "full"
    )

    workspace = initialize_workspace(
        output_path,
        batch_size=batch_size,
        stage2_required=stage2_required,
        resume=resume,
    )

    state = read_state(
        workspace
    )


    if resume and state.get(
        "completed",
        False,
    ):
        return {
            "documents": 0,
            "annotations": 0,
            "relations": 0,
            "batches": 0,
            "batch_size": batch_size,
            "elapsed_seconds": (
                perf_counter() - started
            ),
            "resumed": True,
            "already_completed": True,
        }

    input_documents = (
        count_corpus_input_documents(
            input_path,
            input_format=input_format,
            text_column=text_column,
            id_column=id_column,
            sep=sep,
        )
    )

    summary = _run_stage1(
        pipeline=pipeline,
        pipeline_context=pipeline_context,
        workspace=workspace,
        input_path=input_path,
        input_format=input_format,
        text_column=text_column,
        id_column=id_column,
        sep=sep,
        batch_size=batch_size,
        input_documents=input_documents,
        show_progress=show_progress,
        resume=resume,
    )

    stage2_summary = None

    if metrics["stage2_required"]:
        stage2_summary = _run_stage2(
            workspace=workspace,
            metrics=metrics,
            pipeline_context=(
                pipeline_context
            ),
            config=config,
            output_profile=output_profile,
            show_progress=show_progress,
            resume=resume,
        )

        final_batch_directory = (
            workspace.stage2
        )

    elif output_profile == "full":
        final_batch_directory = (
            workspace.stage1
        )

    else:
        _build_profiled_stage2(
            workspace=workspace,
            output_profile=output_profile,
            resume=resume,
        )

        final_batch_directory = (
            workspace.stage2
        )

        state = read_state(
            workspace
        )

        state["stage2_complete"] = True

        write_state(
            workspace,
            state,
        )

    assemble_batches(
        final_batch_directory,
        output_path,
    )

    _mark_workspace_completed(
        workspace
    )

    summary["elapsed_seconds"] = (
        perf_counter() - started
    )

    summary["resumed"] = resume
    summary["already_completed"] = False

    summary["stage1"] = {
        "processed_batches": summary[
            "processed_batches"
        ],
        "reused_batches": summary[
            "reused_batches"
        ],
    }

    if stage2_summary is not None:
        summary["stage2"] = (
            stage2_summary
        )

    summary.pop(
        "processed_batches",
        None,
    )

    summary.pop(
        "reused_batches",
        None,
    )

    return summary


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
    extended_config = metrics_config.get(
        "extended_tfidf",
        {},
    )

    if not extended_config.get(
        "enabled",
        False,
    ):
        return corpus

    scorer = _build_extended_tfidf_scorer(
        extended_config=extended_config,
        ontology_path=ontology_path,
        config=config,
    )

    return scorer.score(
        corpus
    )


def _build_extended_tfidf_scorer(
    *,
    extended_config: dict,
    ontology_path: str | None,
    config: dict,
) -> ExtendedTfidfScorer:
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

    decay_config = extended_config.get(
        "decay",
        {},
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
    )


def _build_profiled_stage2(
    *,
    workspace,
    output_profile: str,
    resume: bool = False,
) -> None:
    stage1_batches = sorted(
        workspace.stage1.glob(
            "batch_*.jsonl"
        )
    )

    completed_batches = (
        list_completed_batches(
            workspace.stage2
        )
        if resume
        else set()
    )

    for batch_index, batch_file in enumerate(
        stage1_batches,
        start=1,
    ):
        if batch_index in completed_batches:
            continue

        lines = []

        with batch_file.open(
            "r",
            encoding="utf-8",
        ) as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                document = deserialize_document(
                    json.loads(
                        line
                    )
                )

                serialized = serialize_document(
                    document,
                    output_profile=output_profile,
                )

                lines.append(
                    json.dumps(
                        serialized,
                        ensure_ascii=False,
                    )
                )

        write_batch_atomic(
            workspace.stage2,
            batch_index,
            lines,
        )

def _resolve_metrics_config(
    config: dict,
) -> dict:
    metrics_config = config.get(
        "metrics",
        {},
    )

    tfidf = metrics_config.get(
        "tfidf",
        {},
    )

    extended = metrics_config.get(
        "extended_tfidf",
        {},
    )

    tfidf_enabled = tfidf.get(
        "enabled",
        False,
    )

    extended_enabled = extended.get(
        "enabled",
        False,
    )

    if extended_enabled and not tfidf_enabled:
        raise ValueError(
            "extended_tfidf requires tfidf "
            "to be enabled because it propagates "
            "TF-IDF annotation scores."
        )

    return {
        "tfidf": tfidf,
        "extended": extended,
        "tfidf_enabled": tfidf_enabled,
        "extended_enabled": extended_enabled,
        "stage2_required": (
            tfidf_enabled
            or extended_enabled
        ),
    }

def _run_stage1(
    *,
    pipeline,
    pipeline_context: dict,
    workspace,
    input_path: str,
    input_format: str | None,
    text_column: str,
    id_column: str,
    sep: str,
    batch_size: int,
    input_documents: int | None,
    show_progress: bool,
    resume: bool,
) -> dict:
    expected_batches = (
        ceil(
            input_documents / batch_size
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
        batch_size=batch_size,
    )

    completed_batches = (
        list_completed_batches(
            workspace.stage1
        )
        if resume
        else set()
    )

    total_documents = 0
    total_annotations = 0
    total_relations = 0
    total_batches = 0

    with tqdm(
        total=expected_batches,
        desc="Pass 1",
        unit="batch",
        disable=not show_progress,
        dynamic_ncols=True,
    ) as progress:
        for batch_index, corpus in enumerate(
            batches,
            start=1,
        ):
            if batch_index in completed_batches:
                progress.update(1)
                continue

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

            lines = []

            for document in corpus.documents:
                serialized = serialize_document(
                    document,
                    output_profile="full",
                )

                lines.append(
                    json.dumps(
                        serialized,
                        ensure_ascii=False,
                    )
                )

            write_batch_atomic(
                workspace.stage1,
                batch_index,
                lines,
            )

            total_batches += 1
            total_documents += (
                batch_documents
            )

            total_annotations += sum(
                len(document.annotations)
                for document
                in corpus.documents
            )

            total_relations += sum(
                len(document.relations)
                for document
                in corpus.documents
            )

            progress.update(1)

    state = read_state(
        workspace
    )

    state["stage1_complete"] = True

    write_state(
        workspace,
        state,
    )

    return {
        "documents": total_documents,
        "annotations": total_annotations,
        "relations": total_relations,
        "batches": total_batches,
        "batch_size": batch_size,
        "processed_batches": total_batches,
        "reused_batches": len(
            completed_batches
        ),
    }

def _run_stage2(
    *,
    workspace,
    metrics: dict,
    pipeline_context: dict,
    config: dict,
    output_profile: str,
    show_progress: bool,
    resume: bool,
) -> dict:
    tfidf_config = metrics[
        "tfidf"
    ]

    extended_config = metrics[
        "extended"
    ]

    extended_enabled = metrics[
        "extended_enabled"
    ]

    tfidf_layer = tfidf_config.get(
        "layer",
        "ontology",
    )

    stage1_batches = sorted(
        workspace.stage1.glob(
            "batch_*.jsonl"
        )
    )

    #
    # Global TF-IDF statistics
    #

    total_metric_documents = 0
    document_frequency = Counter()

    for batch_file in stage1_batches:
        (
            batch_total,
            batch_df,
        ) = collect_tfidf_statistics(
            str(batch_file),
            layer=tfidf_layer,
        )

        total_metric_documents += (
            batch_total
        )

        document_frequency.update(
            batch_df
        )

    tfidf_scorer = TfidfScorer(
        layer=tfidf_layer,
    )

    tfidf_scorer.fit_statistics(
        total_documents=(
            total_metric_documents
        ),
        document_frequency=(
            document_frequency
        ),
    )

    #
    # Optional ontology expansion
    #

    extended_scorer = None

    if extended_enabled:
        extended_scorer = (
            _build_extended_tfidf_scorer(
                extended_config=(
                    extended_config
                ),
                ontology_path=(
                    pipeline_context[
                        "ontology_path"
                    ]
                ),
                config=config,
            )
        )

    completed_batches = (
        list_completed_batches(
            workspace.stage2
        )
        if resume
        else set()
    )

    #
    # Apply metrics batch by batch
    #

    processed_batches = 0

    with tqdm(
        total=len(stage1_batches),
        desc="Pass 2",
        unit="batch",
        disable=not show_progress,
        dynamic_ncols=True,
    ) as progress:
        for batch_index, batch_file in enumerate(
            stage1_batches,
            start=1,
        ):
            if batch_index in completed_batches:
                progress.update(1)
                continue

            lines = []

            with batch_file.open(
                "r",
                encoding="utf-8",
            ) as f:
                for line in f:
                    line = line.strip()

                    if not line:
                        continue

                    document = (
                        deserialize_document(
                            json.loads(
                                line
                            )
                        )
                    )

                    tfidf_scorer.score_document(
                        document
                    )

                    if (
                        extended_scorer
                        is not None
                    ):
                        extended_scorer.score_document(
                            document
                        )

                    serialized = serialize_document(
                        document,
                        output_profile=(
                            output_profile
                        ),
                    )

                    lines.append(
                        json.dumps(
                            serialized,
                            ensure_ascii=False,
                        )
                    )

            write_batch_atomic(
                workspace.stage2,
                batch_index,
                lines,
            )

            processed_batches += 1

            progress.update(1)

    state = read_state(
        workspace
    )

    state["stage2_complete"] = True

    write_state(
        workspace,
        state,
    )

    return {
        "processed_batches": processed_batches,
        "reused_batches": len(
            completed_batches
        ),
    }

def _mark_workspace_completed(
    workspace,
) -> None:
    state = read_state(
        workspace
    )

    state["status"] = "completed"
    state["completed"] = True

    write_state(
        workspace,
        state,
    )