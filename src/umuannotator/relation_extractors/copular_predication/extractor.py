from __future__ import annotations

from typing import Any

from umuannotator.document import (
    Document,
    Relation,
)

from umuannotator.relation_extractors.stanza_dependency.builders import (
    build_argument,
    build_predicate,
)
from umuannotator.relation_extractors.stanza_dependency.syntax import (
    build_children_index,
    find_dependent,
    get_polarity,
)


class CopularPredicationRelationExtractor:
    def __init__(
        self,
        *,
        metadata_key: str = "stanza",
        source: str = "copular-predication",
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
                document=document,
                sentence=sentence,
            )

        return document

    def _extract_sentence_relations(
        self,
        *,
        document: Document,
        sentence: dict[str, Any],
    ) -> None:
        words = sentence.get(
            "words",
            [],
        )

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
            if predicate_word.get("upos") not in {
                "ADJ",
                "NOUN",
                "PROPN",
            }:
                continue

            predicate_id = predicate_word["id"]

            copula = find_dependent(
                words,
                head=predicate_id,
                deprel="cop",
            )

            if copula is None:
                continue

            subject = find_dependent(
                words,
                head=predicate_id,
                deprel="nsubj",
            )

            if subject is None:
                continue

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
            ]

            relation = Relation(
                type="predicate_argument",
                predicate=predicate,
                arguments=arguments,
                source=self.source,
                metadata={
                    "sentence_id": sentence.get("id"),
                    "rule": "copular_predication",
                    "copula": copula.get("lemma"),
                    "copula_text": copula.get("text"),
                    "polarity": get_polarity(
                        words,
                        predicate_id=predicate_id,
                    ),
                },
            )

            document.add_relation(
                relation
            )