from __future__ import annotations

from typing import Any

from umuannotator.document import (
    Document,
    Relation,
)

from .builders import (
    build_argument,
    build_predicate,
)
from .syntax import (
    build_children_index,
    find_dependent,
    find_inherited_subject,
    get_polarity,
)


class StanzaDependencyRelationExtractor:
    def __init__(
        self,
        *,
        metadata_key: str = "stanza",
        source: str = "stanza-dependency",
    ):
        self.metadata_key = metadata_key
        self.source = source

    def extract(
        self,
        document: Document,
    ) -> Document:
        stanza_data = document.metadata.get(
            self.metadata_key,
            {},
        )

        sentences = stanza_data.get(
            "sentences",
            [],
        )

        for sentence in sentences:
            self._extract_sentence_relations(
                document,
                sentence,
            )

        return document

    def _extract_sentence_relations(
        self,
        document: Document,
        sentence: dict[str, Any],
    ) -> None:
        words = sentence.get("words", [])

        if not words:
            return

        words_by_id = {
            word["id"]: word
            for word in words
        }

        children_by_head = build_children_index(
            words
        )

        for predicate_word in words:
            if predicate_word.get("upos") != "VERB":
                continue

            predicate_id = predicate_word["id"]

            passive_subject = find_dependent(
                words,
                head=predicate_id,
                deprel="nsubj:pass",
            )

            passive_agent = find_dependent(
                words,
                head=predicate_id,
                deprel="obl:agent",
            )

            if (
                passive_subject is not None
                and passive_agent is not None
            ):
                self._add_passive_relation(
                    document=document,
                    sentence=sentence,
                    predicate_word=predicate_word,
                    patient=passive_subject,
                    agent=passive_agent,
                    words=words,
                    words_by_id=words_by_id,
                    children_by_head=children_by_head,
                )
                continue

            subject = find_dependent(
                words,
                head=predicate_id,
                deprel="nsubj",
            )

            subject_inherited_from = None
            subject_inheritance = None

            if subject is None:
                (
                    subject,
                    subject_inherited_from,
                    subject_inheritance,
                ) = find_inherited_subject(
                    predicate_word=predicate_word,
                    words=words,
                    words_by_id=words_by_id,
                )

            object_ = find_dependent(
                words,
                head=predicate_id,
                deprel="obj",
            )

            oblique_argument = find_dependent(
                words,
                head=predicate_id,
                deprel="obl:arg",
            )

            clausal_complement = find_dependent(
                words,
                head=predicate_id,
                deprel="ccomp",
            )

            if (
                subject is not None
                and subject_inherited_from is None
                and object_ is None
                and clausal_complement is not None
            ):
                self._add_ccomp_relation(
                    document=document,
                    sentence=sentence,
                    predicate_word=predicate_word,
                    subject=subject,
                    clausal_complement=clausal_complement,
                    words=words,
                    words_by_id=words_by_id,
                    children_by_head=children_by_head,
                )
                continue

            if subject is None or object_ is None:
                continue

            self._add_active_relation(
                document=document,
                sentence=sentence,
                predicate_word=predicate_word,
                subject=subject,
                object_=object_,
                oblique_argument=oblique_argument,
                subject_inherited_from=subject_inherited_from,
                subject_inheritance=subject_inheritance,
                words=words,
                words_by_id=words_by_id,
                children_by_head=children_by_head,
            )

    def _add_active_relation(
        self,
        *,
        document: Document,
        sentence: dict[str, Any],
        predicate_word: dict[str, Any],
        subject: dict[str, Any],
        object_: dict[str, Any],
        oblique_argument: dict[str, Any] | None,
        subject_inherited_from: int | None,
        subject_inheritance: str | None,
        words: list[dict[str, Any]],
        words_by_id: dict[int, dict[str, Any]],
        children_by_head: dict[int, list[int]],
    ) -> None:
        predicate = build_predicate(
            document=document,
            predicate_word=predicate_word,
        )

        arguments = [
            build_argument(
                document=document,
                word=subject,
                role="subject",
                words_by_id=words_by_id,
                children_by_head=children_by_head,
            ),
            build_argument(
                document=document,
                word=object_,
                role="object",
                words_by_id=words_by_id,
                children_by_head=children_by_head,
            ),
        ]

        if oblique_argument is not None:
            arguments.append(
                build_argument(
                    document=document,
                    word=oblique_argument,
                    role="oblique_argument",
                    words_by_id=words_by_id,
                    children_by_head=children_by_head,
                )
            )

        relation_metadata: dict[str, Any] = {
            "sentence_id": sentence.get("id"),
            "rule": "verb_nsubj_obj",
            "polarity": get_polarity(
                words,
                predicate_id=predicate_word["id"],
            ),
        }

        if subject_inherited_from is not None:
            relation_metadata["subject_inherited"] = True
            relation_metadata[
                "subject_inherited_from_word_id"
            ] = subject_inherited_from

            relation_metadata[
                "subject_inheritance"
            ] = subject_inheritance

        relation = Relation(
            type="predicate_argument",
            predicate=predicate,
            arguments=arguments,
            source=self.source,
            metadata=relation_metadata,
        )

        document.add_relation(relation)

    def _add_passive_relation(
        self,
        *,
        document: Document,
        sentence: dict[str, Any],
        predicate_word: dict[str, Any],
        patient: dict[str, Any],
        agent: dict[str, Any],
        words: list[dict[str, Any]],
        words_by_id: dict[int, dict[str, Any]],
        children_by_head: dict[int, list[int]],
    ) -> None:
        predicate = build_predicate(
            document=document,
            predicate_word=predicate_word,
        )

        arguments = [
            build_argument(
                document=document,
                word=patient,
                role="patient",
                words_by_id=words_by_id,
                children_by_head=children_by_head,
            ),
            build_argument(
                document=document,
                word=agent,
                role="agent",
                words_by_id=words_by_id,
                children_by_head=children_by_head,
            ),
        ]

        relation = Relation(
            type="predicate_argument",
            predicate=predicate,
            arguments=arguments,
            source=self.source,
            metadata={
                "sentence_id": sentence.get("id"),
                "rule": "verb_passive_agent",
                "voice": "passive",
                "polarity": get_polarity(
                    words,
                    predicate_id=predicate_word["id"],
                ),
            },
        )

        document.add_relation(relation)


    def _add_ccomp_relation(
        self,
        *,
        document: Document,
        sentence: dict[str, Any],
        predicate_word: dict[str, Any],
        subject: dict[str, Any],
        clausal_complement: dict[str, Any],
        words: list[dict[str, Any]],
        words_by_id: dict[int, dict[str, Any]],
        children_by_head: dict[int, list[int]],
    ) -> None:
        predicate = build_predicate(
            document=document,
            predicate_word=predicate_word,
        )

        arguments = [
            build_argument(
                document=document,
                word=subject,
                role="subject",
                words_by_id=words_by_id,
                children_by_head=children_by_head,
            ),
            build_argument(
                document=document,
                word=clausal_complement,
                role="clausal_complement",
                words_by_id=words_by_id,
                children_by_head=children_by_head,
            ),
        ]

        relation = Relation(
            type="predicate_argument",
            predicate=predicate,
            arguments=arguments,
            source=self.source,
            metadata={
                "sentence_id": sentence.get("id"),
                "rule": "verb_nsubj_ccomp",
                "polarity": get_polarity(
                    words,
                    predicate_id=predicate_word["id"],
                ),
            },
        )

        document.add_relation(relation)