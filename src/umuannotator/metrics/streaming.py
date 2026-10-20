from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from umuannotator.metrics.extended_tfidf import ExtendedTfidfScorer
from umuannotator.metrics.tfidf import TfidfScorer
from umuannotator.serialization.documents import (
    deserialize_document,
    serialize_document,
)


def collect_tfidf_statistics(
    input_path: str,
    *,
    layer: str = "ontology",
) -> tuple[int, Counter[str]]:
    """
    Collect corpus-level TF-IDF statistics from an annotated JSONL file.

    Returns:
        total_documents
        document_frequency
    """
    total_documents = 0
    document_frequency: Counter[str] = Counter()

    path = Path(input_path)

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            document = json.loads(line)

            total_documents += 1

            labels_in_document = {
                annotation["label"]
                for annotation in document.get(
                    "annotations",
                    [],
                )
                if annotation.get("layer")
                == layer
            }

            for label in labels_in_document:
                document_frequency[label] += 1

    return (
        total_documents,
        document_frequency,
    )


def apply_streaming_tfidf(
    input_path: str,
    output_path: str,
    *,
    tfidf_scorer: TfidfScorer,
    extended_tfidf_scorer: ExtendedTfidfScorer | None = None,
    output_profile: str = "full",
) -> dict:
    """
    Apply TF-IDF and optional ontology-expanded TF-IDF to an annotated
    JSONL corpus using a streaming second pass.

    The input is scanned once to collect global TF-IDF statistics and
    then read again document by document to apply the scores.

    The output JSONL is written incrementally.
    """
    total_documents, document_frequency = (
        collect_tfidf_statistics(
            input_path,
            layer=tfidf_scorer.layer,
        )
    )

    tfidf_scorer.fit_statistics(
        total_documents=total_documents,
        document_frequency=document_frequency,
    )

    input_file = Path(input_path)
    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    processed_documents = 0
    annotations_scored = 0

    with input_file.open(
        "r",
        encoding="utf-8",
    ) as source, output_file.open(
        "w",
        encoding="utf-8",
    ) as target:
        for line in source:
            line = line.strip()

            if not line:
                continue

            data = json.loads(line)

            document = deserialize_document(
                data
            )

            tfidf_scorer.score_document(
                document
            )

            if extended_tfidf_scorer is not None:
                extended_tfidf_scorer.score_document(
                    document
                )

            annotations_scored += sum(
                1
                for annotation in document.annotations
                if annotation.layer
                == tfidf_scorer.layer
            )

            serialized = serialize_document(
                document,
                output_profile=output_profile,
            )

            target.write(
                json.dumps(
                    serialized,
                    ensure_ascii=False,
                )
                + "\n"
            )

            processed_documents += 1

    return {
        "documents": processed_documents,
        "annotations_scored": annotations_scored,
        "tfidf_layer": tfidf_scorer.layer,
        "extended_tfidf": (
            extended_tfidf_scorer
            is not None
        ),
    }