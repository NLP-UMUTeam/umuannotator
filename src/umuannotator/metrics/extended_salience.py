from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class ExtendedSalienceKey:
    layer: str
    label: str
    canonical: str


@dataclass(frozen=True)
class ExpandedContribution:
    source: str
    target: str
    distance: int
    contribution: float


def compute_extended_salience(
    data: dict[str, Any],
    *,
    ontology_graph: dict[str, dict[str, int]],
    top: int = 20,
    layer: str = "ontology",
    max_distance: int = 2,
    decay: float = 0.5,
    direction: str = "outgoing",
) -> dict[str, Any]:
    """
    Compute TF-IDF-e over ontology annotations.

    Observed annotations contribute their TF-IDF score to their own concept.
    That score is also propagated to related ontology concepts using:

        contribution = observed_score * decay ** distance

    ontology_graph is expected to map:

        source_concept_uri -> {target_concept_uri: distance}
    """
    documents = data.get("documents", [])
    total_documents = len(documents)

    tf: Counter[str] = Counter()
    document_frequency: Counter[str] = Counter()
    displays: dict[str, Counter[str]] = defaultdict(Counter)
    labels: dict[str, Counter[str]] = defaultdict(Counter)

    for document in documents:
        seen_in_document: set[str] = set()

        for annotation in document.get("annotations", []):
            if annotation.get("layer") != layer:
                continue

            concept_uri = _concept_uri(annotation)

            if not concept_uri:
                continue

            tf[concept_uri] += 1
            seen_in_document.add(concept_uri)
            displays[concept_uri][str(annotation.get("text", ""))] += 1
            labels[concept_uri][str(annotation.get("label", ""))] += 1

        for concept_uri in seen_in_document:
            document_frequency[concept_uri] += 1

    observed_scores: dict[str, float] = {}
    idfs: dict[str, float] = {}

    for concept_uri, term_frequency in tf.items():
        df = document_frequency[concept_uri]
        idf = _idf(
            total_documents=total_documents,
            document_frequency=df,
        )

        idfs[concept_uri] = idf
        observed_scores[concept_uri] = term_frequency * idf

    expanded_scores: Counter[str] = Counter()
    contributions: dict[str, list[ExpandedContribution]] = defaultdict(list)

    for source_uri, observed_score in observed_scores.items():
        for target_uri, distance in _iter_expansion_targets(
            source_uri,
            ontology_graph=ontology_graph,
            max_distance=max_distance,
        ):
            contribution = observed_score * (decay**distance)

            expanded_scores[target_uri] += contribution
            contributions[target_uri].append(
                ExpandedContribution(
                    source=source_uri,
                    target=target_uri,
                    distance=distance,
                    contribution=contribution,
                )
            )

    all_uris = set(observed_scores) | set(expanded_scores)

    rows = []

    for concept_uri in all_uris:
        observed_score = observed_scores.get(concept_uri, 0.0)
        expanded_score = expanded_scores.get(concept_uri, 0.0)
        total_score = observed_score + expanded_score

        rows.append(
            {
                "canonical": f"concept_uri:{concept_uri}",
                "concept_uri": concept_uri,
                "layer": layer,
                "label": _most_common(labels.get(concept_uri)),
                "display": _most_common(displays.get(concept_uri)),
                "tf": tf.get(concept_uri, 0),
                "df": document_frequency.get(concept_uri, 0),
                "idf": idfs.get(concept_uri, 0.0),
                "observed_score": observed_score,
                "expanded_score": expanded_score,
                "score": total_score,
                "expanded_from": [
                    {
                        "source": contribution.source,
                        "distance": contribution.distance,
                        "contribution": contribution.contribution,
                    }
                    for contribution in sorted(
                        contributions.get(concept_uri, []),
                        key=lambda item: (
                            item.distance,
                            -item.contribution,
                            item.source,
                        ),
                    )
                ],
            }
        )

    rows = sorted(
        rows,
        key=lambda row: (
            row["score"],
            row["observed_score"],
            row["expanded_score"],
            row["tf"],
            row["display"],
        ),
        reverse=True,
    )

    return {
        "documents": total_documents,
        "method": "tfidf-e",
        "layer": layer,
        "max_distance": max_distance,
        "decay": decay,
        "direction": direction,
        "items": rows[:top],
    }


def _concept_uri(
    annotation: dict[str, Any],
) -> str | None:
    metadata = annotation.get("metadata", {}) or {}
    value = metadata.get("concept_uri")

    if value:
        return str(value)

    return None


def _iter_expansion_targets(
    source_uri: str,
    *,
    ontology_graph: dict[str, dict[str, int]],
    max_distance: int,
):
    for target_uri, distance in ontology_graph.get(source_uri, {}).items():
        if distance <= 0:
            continue

        if distance > max_distance:
            continue

        yield target_uri, distance


def _idf(
    *,
    total_documents: int,
    document_frequency: int,
) -> float:
    if total_documents <= 0:
        return 0.0

    return math.log(
        (total_documents + 1) / (document_frequency + 1),
    ) + 1


def _most_common(
    counter: Counter[str] | None,
) -> str:
    if not counter:
        return ""

    return counter.most_common(1)[0][0]