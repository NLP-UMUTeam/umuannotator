from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from umuannotator.document import (
    Document,
    Relation,
    RelationArgument,
    RelationPredicate,
)


class ReportedSpeechRelationExtractor:
    def __init__(
        self,
        *,
        source: str,
    ):
        self.source = source

        config = self._load_config(source)
        self.reporting_lemmas = self._load_reporting_lemmas(
            config
        )

    def extract(
        self,
        document: Document,
    ) -> Document:
        relations = list(document.relations)

        for relation in relations:
            self._process_relation(
                document,
                relation,
            )

        return document

    def _process_relation(
        self,
        document: Document,
        relation: Relation,
    ) -> None:
        if relation.type != "predicate_argument":
            return

        predicate_lemma = relation.predicate.lemma

        if not isinstance(predicate_lemma, str):
            return

        predicate_lemma = predicate_lemma.lower()

        if predicate_lemma not in self.reporting_lemmas:
            return

        subject = self._find_argument(
            relation,
            role="subject",
        )

        clausal_complement = self._find_argument(
            relation,
            role="clausal_complement",
        )

        if (
            subject is None
            or clausal_complement is None
        ):
            return

        speech_type = self._detect_speech_type(
            clausal_complement
        )

        if speech_type == "direct":
            content = self._clean_direct_content(
                clausal_complement
            )
        else:
            content = clausal_complement

        reported_speech = Relation(
            type="reported_speech",
            predicate=self._copy_predicate(
                relation.predicate
            ),
            arguments=[
                self._copy_argument(
                    subject,
                    role="speaker",
                ),
                self._copy_argument(
                    content,
                    role="content",
                ),
            ],
            source=self.source,
            score=relation.score,
            metadata={
                "derived_from": "predicate_argument",
                "reporting_lemma": predicate_lemma,
                "source_relation_rule": (
                    relation.metadata.get("rule")
                ),
                "sentence_id": (
                    relation.metadata.get("sentence_id")
                ),
                "speech_type": speech_type,
            },
        )

        document.add_relation(
            reported_speech
        )

    @staticmethod
    def _load_config(
        source: str,
    ) -> dict[str, Any]:
        with Path(source).open(
            "r",
            encoding="utf-8",
        ) as file:
            return yaml.safe_load(file) or {}

    @staticmethod
    def _load_reporting_lemmas(
        config: dict[str, Any],
    ) -> set[str]:
        raw_lemmas = config.get(
            "reporting_lemmas"
        )

        if raw_lemmas is None:
            raise ValueError(
                "Reported speech config requires "
                "a 'reporting_lemmas' section"
            )

        if not isinstance(raw_lemmas, list):
            raise ValueError(
                "'reporting_lemmas' must be a list"
            )

        lemmas = {
            str(lemma).strip().lower()
            for lemma in raw_lemmas
            if str(lemma).strip()
        }

        if not lemmas:
            raise ValueError(
                "'reporting_lemmas' must contain "
                "at least one lemma"
            )

        return lemmas

    @staticmethod
    def _find_argument(
        relation: Relation,
        *,
        role: str,
    ) -> RelationArgument | None:
        for argument in relation.arguments:
            if argument.role == role:
                return argument

        return None

    @staticmethod
    def _copy_predicate(
        predicate: RelationPredicate,
    ) -> RelationPredicate:
        return RelationPredicate(
            start=predicate.start,
            end=predicate.end,
            text=predicate.text,
            lemma=predicate.lemma,
            metadata=dict(predicate.metadata),
        )

    @staticmethod
    def _copy_argument(
        argument: RelationArgument,
        *,
        role: str,
    ) -> RelationArgument:
        return RelationArgument(
            role=role,
            start=argument.start,
            end=argument.end,
            text=argument.text,
            annotation_id=argument.annotation_id,
            metadata=dict(argument.metadata),
        )

    @staticmethod
    def _detect_speech_type(
        content: RelationArgument,
    ) -> str:
        text = content.text

        quote_characters = {
            '"',
            "'",
            "“",
            "”",
            "‘",
            "’",
            "«",
            "»",
        }

        if any(
            character in text
            for character in quote_characters
        ):
            return "direct"

        return "indirect"

    @staticmethod
    def _clean_direct_content(
        argument: RelationArgument,
    ) -> RelationArgument:
        text = argument.text

        left = 0
        right = len(text)

        leading_characters = {
            " ",
            "\t",
            "\n",
            ":",
            ",",
            '"',
            "'",
            "“",
            "”",
            "‘",
            "’",
            "«",
            "»",
        }

        trailing_characters = {
            " ",
            "\t",
            "\n",
            ",",
            ";",
            ":",
            '"',
            "'",
            "“",
            "”",
            "‘",
            "’",
            "«",
            "»",
        }

        while (
            left < right
            and text[left] in leading_characters
        ):
            left += 1

        while (
            right > left
            and text[right - 1] in trailing_characters
        ):
            right -= 1

        return RelationArgument(
            role=argument.role,
            start=argument.start + left,
            end=argument.start + right,
            text=text[left:right],
            annotation_id=argument.annotation_id,
            metadata=dict(argument.metadata),
        )