from __future__ import annotations

from typing import Any

from umuannotator.document import Annotation, Document, RelationArgument


class AnnotationOverlapRelationEnricher:
    def __init__(
        self,
        *,
        match: list[str] | None = None,
    ):
        self.match = match or [
            "exact",
            "contained",
        ]

        valid_matches = {
            "exact",
            "contained",
        }

        unknown = set(self.match) - valid_matches

        if unknown:
            raise ValueError(
                "Unknown annotation-overlap match mode(s): "
                + ", ".join(sorted(unknown))
            )

    def enrich(
        self,
        document: Document,
    ) -> Document:
        for relation in document.relations:
            for argument in relation.arguments:
                self._enrich_argument(
                    argument,
                    document.annotations,
                )

        return document

    def _enrich_argument(
        self,
        argument: RelationArgument,
        annotations: list[Annotation],
    ) -> None:
        enriched_annotations = []

        for annotation in annotations:
            match_type = self._get_match_type(
                argument,
                annotation,
            )

            if match_type is None:
                continue

            enriched_annotations.append(
                self._annotation_to_dict(
                    annotation,
                    match_type=match_type,
                )
            )

        argument.annotations = enriched_annotations

    def _get_match_type(
        self,
        argument: RelationArgument,
        annotation: Annotation,
    ) -> str | None:
        if (
            "exact" in self.match
            and annotation.start == argument.start
            and annotation.end == argument.end
        ):
            return "exact"

        if (
            "contained" in self.match
            and argument.start <= annotation.start
            and annotation.end <= argument.end
        ):
            return "contained"

        return None

    @staticmethod
    def _annotation_to_dict(
        annotation: Annotation,
        *,
        match_type: str,
    ) -> dict[str, Any]:
        return {
            "start": annotation.start,
            "end": annotation.end,
            "text": annotation.text,
            "label": annotation.label,
            "layer": annotation.layer,
            "source": annotation.source,
            "type": annotation.type,
            "subtype": annotation.subtype,
            "score": annotation.score,
            "metadata": dict(annotation.metadata),
            "match": match_type,
        }