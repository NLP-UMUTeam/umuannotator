from __future__ import annotations

from typing import Any

from umuannotator.document import (
    Document,
    Relation,
    RelationArgument,
    RelationPredicate,
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

        children_by_head = self._build_children_index(
            words
        )

        for predicate_word in words:
            if predicate_word.get("upos") != "VERB":
                continue

            predicate_id = predicate_word["id"]

            passive_subject = self._find_dependent(
                words,
                head=predicate_id,
                deprel="nsubj:pass",
            )

            passive_agent = self._find_dependent(
                words,
                head=predicate_id,
                deprel="obl:agent",
            )

            subject = self._find_dependent(
                words,
                head=predicate_id,
                deprel="nsubj",
            )

            subject_inherited_from = None

            if (
                subject is None
                and predicate_word.get("deprel") == "conj"
            ):
                parent_id = predicate_word.get("head")
                parent_word = words_by_id.get(parent_id)

                if (
                    parent_word is not None
                    and parent_word.get("upos") == "VERB"
                ):
                    subject = self._find_dependent(
                        words,
                        head=parent_id,
                        deprel="nsubj",
                    )

                    if subject is not None:
                        subject_inherited_from = parent_id

            object_ = self._find_dependent(
                words,
                head=predicate_id,
                deprel="obj",
            )

            oblique_argument = self._find_dependent(
                words,
                head=predicate_id,
                deprel="obl:arg",
            )

            polarity = self._get_polarity(
                words,
                predicate_id=predicate_id,
            )

            if passive_subject is not None and passive_agent is not None:
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

            if subject is None or object_ is None:
                continue

            subject_span = self._dependency_subtree_span(
                document=document,
                word=subject,
                words_by_id=words_by_id,
                children_by_head=children_by_head,
            )

            object_span = self._dependency_subtree_span(
                document=document,
                word=object_,
                words_by_id=words_by_id,
                children_by_head=children_by_head,
            )

            predicate = RelationPredicate(
                start=predicate_word["start"],
                end=predicate_word["end"],
                text=document.text[
                    predicate_word["start"]:
                    predicate_word["end"]
                ],
                lemma=predicate_word.get("lemma"),
                metadata={
                    "word_id": predicate_word["id"],
                },
            )

            arguments = [
                RelationArgument(
                    role="subject",
                    start=subject_span["start"],
                    end=subject_span["end"],
                    text=subject_span["text"],
                    metadata={
                        "head_word_id": subject["id"],
                        "deprel": subject.get("deprel"),
                    },
                ),
                RelationArgument(
                    role="object",
                    start=object_span["start"],
                    end=object_span["end"],
                    text=object_span["text"],
                    metadata={
                        "head_word_id": object_["id"],
                        "deprel": object_.get("deprel"),
                    },
                ),
            ]

            if oblique_argument is not None:
                oblique_span = self._dependency_subtree_span(
                    document=document,
                    word=oblique_argument,
                    words_by_id=words_by_id,
                    children_by_head=children_by_head,
                )

                arguments.append(
                    RelationArgument(
                        role="oblique_argument",
                        start=oblique_span["start"],
                        end=oblique_span["end"],
                        text=oblique_span["text"],
                        metadata={
                            "head_word_id": oblique_argument["id"],
                            "deprel": oblique_argument.get("deprel"),
                        },
                    )
                )

            relation_metadata = {
                "sentence_id": sentence.get("id"),
                "rule": "verb_nsubj_obj",
                "polarity": polarity,
            }

            if subject_inherited_from is not None:
                relation_metadata["subject_inherited"] = True
                relation_metadata["subject_inherited_from_word_id"] = (
                    subject_inherited_from
                )

            relation = Relation(
                type="predicate_argument",
                predicate=predicate,
                arguments=arguments,
                source=self.source,
                metadata=relation_metadata,
            )

            document.add_relation(relation)

    @staticmethod
    def _find_dependent(
        words: list[dict[str, Any]],
        *,
        head: int,
        deprel: str,
    ) -> dict[str, Any] | None:
        for word in words:
            if (
                word.get("head") == head
                and word.get("deprel") == deprel
            ):
                return word

        return None

    @staticmethod
    def _build_children_index(
        words: list[dict[str, Any]],
    ) -> dict[int, list[int]]:
        children_by_head: dict[int, list[int]] = {}

        for word in words:
            head = word.get("head")

            if head is None:
                continue

            children_by_head.setdefault(
                head,
                [],
            ).append(word["id"])

        return children_by_head

    def _dependency_subtree_span(
        self,
        *,
        document: Document,
        word: dict[str, Any],
        words_by_id: dict[int, dict[str, Any]],
        children_by_head: dict[int, list[int]],
    ) -> dict[str, Any]:
        subtree_ids = self._collect_subtree_ids(
            word["id"],
            children_by_head,
        )

        subtree_words = [
            words_by_id[word_id]
            for word_id in subtree_ids
            if word_id in words_by_id
        ]

        subtree_words = [
            item
            for item in subtree_words
            if item.get("start") is not None
            and item.get("end") is not None
        ]

        if not subtree_words:
            return {
                "start": word["start"],
                "end": word["end"],
                "text": document.text[
                    word["start"]:
                    word["end"]
                ],
            }

        start = min(
            item["start"]
            for item in subtree_words
        )

        end = max(
            item["end"]
            for item in subtree_words
        )

        return {
            "start": start,
            "end": end,
            "text": document.text[start:end],
        }

    def _collect_subtree_ids(
        self,
        word_id: int,
        children_by_head: dict[int, list[int]],
    ) -> set[int]:
        result = {word_id}

        for child_id in children_by_head.get(
            word_id,
            [],
        ):
            result.update(
                self._collect_subtree_ids(
                    child_id,
                    children_by_head,
                )
            )

        return result

    @staticmethod
    def _get_polarity(
        words: list[dict[str, Any]],
        *,
        predicate_id: int,
    ) -> str:
        for word in words:
            if word.get("head") != predicate_id:
                continue

            feats = word.get("feats") or ""

            if "Polarity=Neg" in feats:
                return "negative"

            lemma = word.get("lemma")

            if (
                isinstance(lemma, str)
                and lemma.lower() == "no"
            ):
                return "negative"

        return "positive"

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
        patient_span = self._dependency_subtree_span(
            document=document,
            word=patient,
            words_by_id=words_by_id,
            children_by_head=children_by_head,
        )

        agent_span = self._dependency_subtree_span(
            document=document,
            word=agent,
            words_by_id=words_by_id,
            children_by_head=children_by_head,
        )

        predicate = RelationPredicate(
            start=predicate_word["start"],
            end=predicate_word["end"],
            text=document.text[
                predicate_word["start"]:predicate_word["end"]
            ],
            lemma=predicate_word.get("lemma"),
            metadata={
                "word_id": predicate_word["id"],
            },
        )

        arguments = [
            RelationArgument(
                role="patient",
                start=patient_span["start"],
                end=patient_span["end"],
                text=patient_span["text"],
                metadata={
                    "head_word_id": patient["id"],
                    "deprel": patient.get("deprel"),
                },
            ),
            RelationArgument(
                role="agent",
                start=agent_span["start"],
                end=agent_span["end"],
                text=agent_span["text"],
                metadata={
                    "head_word_id": agent["id"],
                    "deprel": agent.get("deprel"),
                },
            ),
        ]

        polarity = self._get_polarity(
            words,
            predicate_id=predicate_word["id"],
        )

        relation = Relation(
            type="predicate_argument",
            predicate=predicate,
            arguments=arguments,
            source=self.source,
            metadata={
                "sentence_id": sentence.get("id"),
                "rule": "verb_passive_agent",
                "voice": "passive",
                "polarity": polarity,
            },
        )

        document.add_relation(relation)    