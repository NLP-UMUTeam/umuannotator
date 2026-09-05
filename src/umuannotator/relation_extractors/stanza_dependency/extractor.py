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
    find_dependents,
    find_inherited_subject,
    get_polarity,
    is_finite_predicate,
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

            # A passive relation is useful even when the agent
            # is not explicitly expressed.
            if passive_subject is not None:
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

            indirect_object = find_dependent(
                words,
                head=predicate_id,
                deprel="iobj",
            )

            oblique_argument = find_dependent(
                words,
                head=predicate_id,
                deprel="obl:arg",
            )

            generic_obliques = find_dependents(
                words,
                head=predicate_id,
                deprel="obl",
            )

            clausal_complement = find_dependent(
                words,
                head=predicate_id,
                deprel="ccomp",
            )

            open_clausal_complement = find_dependent(
                words,
                head=predicate_id,
                deprel="xcomp",
            )

            # Preserve current xcomp behaviour:
            # do not emit the matrix verb as a subject-only
            # relation when the lexical event is expressed by
            # the open clausal complement.
            if (
                open_clausal_complement is not None
                and object_ is None
            ):
                continue

            # Matrix relation with a clausal complement.
            # The subject may be explicit or inherited from
            # coordination / another supported structure.
            if (
                subject is not None
                and object_ is None
                and clausal_complement is not None
            ):
                self._add_ccomp_relation(
                    document=document,
                    sentence=sentence,
                    predicate_word=predicate_word,
                    subject=subject,
                    clausal_complement=clausal_complement,
                    subject_inherited_from=subject_inherited_from,
                    subject_inheritance=subject_inheritance,
                    words=words,
                    words_by_id=words_by_id,
                    children_by_head=children_by_head,
                )
                continue

            has_core_argument = any(
                argument is not None
                for argument in (
                    subject,
                    object_,
                    indirect_object,
                    oblique_argument,
                )
            )

            has_generic_oblique = bool(
                generic_obliques
            )

            if not has_core_argument:
                if not (
                    has_generic_oblique
                    and is_finite_predicate(
                        predicate_word
                    )
                ):
                    continue

            self._add_active_relation(
                document=document,
                sentence=sentence,
                predicate_word=predicate_word,
                subject=subject,
                object_=object_,
                indirect_object=indirect_object,
                oblique_argument=oblique_argument,
                generic_obliques=generic_obliques,
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
        subject: dict[str, Any] | None,
        object_: dict[str, Any] | None,
        indirect_object: dict[str, Any] | None,
        oblique_argument: dict[str, Any] | None,
        generic_obliques: list[dict[str, Any]],
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

        arguments = []

        if subject is not None:
            arguments.append(
                build_argument(
                    document=document,
                    word=subject,
                    role="subject",
                    words_by_id=words_by_id,
                    children_by_head=children_by_head,
                )
            )

        if object_ is not None:
            arguments.append(
                build_argument(
                    document=document,
                    word=object_,
                    role="object",
                    words_by_id=words_by_id,
                    children_by_head=children_by_head,
                )
            )

        if indirect_object is not None:
            arguments.append(
                build_argument(
                    document=document,
                    word=indirect_object,
                    role="indirect_object",
                    words_by_id=words_by_id,
                    children_by_head=children_by_head,
                )
            )

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

        for generic_oblique in generic_obliques:
            arguments.append(
                build_argument(
                    document=document,
                    word=generic_oblique,
                    role="oblique",
                    words_by_id=words_by_id,
                    children_by_head=children_by_head,
                )
            )

        if subject is not None and object_ is not None:
            rule = "verb_nsubj_obj"

        elif subject is not None:
            rule = "verb_nsubj"

        elif object_ is not None:
            rule = "verb_obj"

        elif indirect_object is not None:
            rule = "verb_iobj"

        elif oblique_argument is not None:
            rule = "verb_obl_arg"

        else:
            rule = "verb_obl"

        relation_metadata: dict[str, Any] = {
            "sentence_id": sentence.get("id"),
            "rule": rule,
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
        agent: dict[str, Any] | None,
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
        ]

        if agent is not None:
            arguments.append(
                build_argument(
                    document=document,
                    word=agent,
                    role="agent",
                    words_by_id=words_by_id,
                    children_by_head=children_by_head,
                )
            )

        rule = (
            "verb_passive_agent"
            if agent is not None
            else "verb_passive"
        )

        relation = Relation(
            type="predicate_argument",
            predicate=predicate,
            arguments=arguments,
            source=self.source,
            metadata={
                "sentence_id": sentence.get("id"),
                "rule": rule,
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
                word=clausal_complement,
                role="clausal_complement",
                words_by_id=words_by_id,
                children_by_head=children_by_head,
            ),
        ]

        relation_metadata: dict[str, Any] = {
            "sentence_id": sentence.get("id"),
            "rule": "verb_nsubj_ccomp",
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