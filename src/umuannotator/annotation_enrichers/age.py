from __future__ import annotations

from typing import Any

from umuannotator.document.model import Annotation, Document


class AgeEnricher:
    def __init__(
        self,
        *,
        temporal_layer: str = "temporal",
        lexical_semantics_layer: str = "lexical_semantics",
    ):
        self.temporal_layer = temporal_layer
        self.lexical_semantics_layer = lexical_semantics_layer

    def enrich(
        self,
        document: Document,
    ) -> Document:
        stanza = document.metadata.get("stanza")

        if not stanza:
            return document

        for annotation in document.annotations:
            if not self._is_duration(annotation):
                continue

            evidence = self._find_age_evidence(
                annotation=annotation,
                document=document,
                stanza=stanza,
            )

            if evidence is None:
                continue

            self._refine_as_age(
                annotation=annotation,
                evidence=evidence,
            )

        return document

    def _is_duration(
        self,
        annotation: Annotation,
    ) -> bool:
        return (
            annotation.layer == self.temporal_layer
            and annotation.label == "DURATION"
        )

    def _find_age_evidence(
        self,
        *,
        annotation: Annotation,
        document: Document,
        stanza: dict[str, Any],
    ) -> dict[str, Any] | None:
        for sentence in stanza.get("sentences", []):
            words = sentence.get("words", [])

            if not words:
                continue

            words_by_id = {
                word["id"]: word
                for word in words
                if word.get("id") is not None
            }

            for word in words:
                if not self._is_duration_noun(
                    word=word,
                    annotation=annotation,
                ):
                    continue

                if not self._has_numeric_modifier(
                    word=word,
                    words=words,
                ):
                    continue

                head = words_by_id.get(
                    word.get("head")
                )

                if head is None:
                    continue

                if not self._is_unambiguously_human(
                    word=head,
                    annotations=document.annotations,
                ):
                    continue

                return {
                    "duration_noun": {
                        "text": word.get("text"),
                        "lemma": word.get("lemma"),
                        "start": word.get("start"),
                        "end": word.get("end"),
                    },
                    "human_head": {
                        "text": head.get("text"),
                        "lemma": head.get("lemma"),
                        "start": head.get("start"),
                        "end": head.get("end"),
                    },
                }

        return None

    def _is_duration_noun(
        self,
        *,
        word: dict[str, Any],
        annotation: Annotation,
    ) -> bool:
        start = word.get("start")
        end = word.get("end")

        if start is None or end is None:
            return False

        return (
            word.get("upos") == "NOUN"
            and word.get("deprel") == "nmod"
            and annotation.start <= start
            and end <= annotation.end
        )

    def _has_numeric_modifier(
        self,
        *,
        word: dict[str, Any],
        words: list[dict[str, Any]],
    ) -> bool:
        word_id = word.get("id")

        return any(
            candidate.get("head") == word_id
            and candidate.get("deprel") == "nummod"
            for candidate in words
        )

    def _is_unambiguously_human(
        self,
        *,
        word: dict[str, Any],
        annotations: list[Annotation],
    ) -> bool:
        start = word.get("start")
        end = word.get("end")

        if start is None or end is None:
            return False

        for annotation in annotations:
            if annotation.layer != self.lexical_semantics_layer:
                continue

            if (
                annotation.start != start
                or annotation.end != end
            ):
                continue

            synset_classes = annotation.metadata.get(
                "synset_classes",
                {},
            )

            if not synset_classes:
                return False

            return all(
                classes == ["HUMAN"]
                for classes in synset_classes.values()
            )

        return False

    def _refine_as_age(
        self,
        *,
        annotation: Annotation,
        evidence: dict[str, Any],
    ) -> None:
        original_label = annotation.label

        annotation.label = "AGE"

        annotation.metadata["resolved_from"] = original_label
        annotation.metadata["refined_by"] = "age"
        annotation.metadata["rule"] = "human_nominal_age"
        annotation.metadata["age_evidence"] = evidence