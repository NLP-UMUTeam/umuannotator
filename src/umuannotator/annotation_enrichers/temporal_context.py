from __future__ import annotations

from datetime import datetime
from typing import Any

import pendulum
import re

from umuannotator.document.model import Annotation, Document

from umuannotator.lang.temporal import (
    TemporalLanguageRules,
    get_temporal_rules,
)


class TemporalContextEnricher:
    """Refine temporal annotations using document context.

    Contextual corrections are intentionally conservative. An annotation
    is modified only when the available evidence supports a substantially
    safer interpretation than the original one.
    """

    def __init__(
        self,
        language: str = "es",
        reference_datetime_metadata_key: str = "source.publication_date",
        max_past_days: int = 90,
    ) -> None:
        self.language = language
        self.rules: TemporalLanguageRules = get_temporal_rules(language)
        self.reference_datetime_metadata_key = (
            reference_datetime_metadata_key
        )
        self.max_past_days = max_past_days

    def enrich(self, document: Document) -> Document:
        reference_datetime = self._resolve_reference_datetime(document)

        if reference_datetime is None:
            return document

        # First refine DATE annotations. Later contextual rules must consume
        # these final normalized dates rather than the original Duckling
        # resolutions.
        for annotation in document.annotations:
            if annotation.layer != "temporal":
                continue

            if annotation.label != "DATE":
                continue

            self._refine_day_month_without_year(
                document,
                annotation,
                reference_datetime,
            )

            self._refine_weekday(
                document,
                annotation,
                reference_datetime,
            )

            self._refine_month_without_year(
                document,
                annotation,
                reference_datetime,
            )

            self._refine_relative_time_as_duration(
                document,
                annotation,
                reference_datetime,
            )

        # Resolve standalone clock times only after DATE annotations have
        # received all contextual corrections.
        for annotation in document.annotations:
            if annotation.layer != "temporal":
                continue

            if annotation.label != "TIME":
                continue

            self._refine_time_from_contextual_date(
                document,
                annotation,
            )

        return document

    def _refine_day_month_without_year(
        self,
        document: Document,
        annotation: Annotation,
        reference_datetime: pendulum.DateTime,
    ) -> None:
        components = self._extract_day_month_without_year(annotation)

        if components is None:
            return

        day, month = components

        normalized = annotation.metadata.get("normalized")
        if not isinstance(normalized, str):
            return

        try:
            resolved = pendulum.parse(normalized)
        except (ValueError, TypeError):
            return

        # This rule only considers future Duckling resolutions that may
        # actually refer to a recent past date.
        if resolved <= reference_datetime:
            return

        try:
            candidate = reference_datetime.replace(
                month=month,
                day=day,
            )
        except ValueError:
            return

        if candidate > reference_datetime:
            return

        distance_days = (
            reference_datetime.date() - candidate.date()
        ).days

        if distance_days > self.max_past_days:
            return

        predicate_context = self._get_temporal_predicate_context(
            document,
            annotation,
        )

        temporal_orientation = self._classify_temporal_orientation(
            predicate_context,
        )

        # A contextual correction that contradicts Duckling is only
        # applied when the local predicate context provides explicit
        # evidence that the temporal expression belongs to the past.
        if temporal_orientation != "PAST":
            return

        previous_normalized = normalized

        annotation.metadata["normalized"] = (
            self._preserve_time_and_timezone(
                resolved,
                candidate,
            )
        )

        annotation.metadata["context_resolution"] = {
            "rule": "day_month_recent_past",
            "previous_normalized": previous_normalized,
            "reference_datetime": (
                reference_datetime.to_iso8601_string()
            ),
            "distance_days": distance_days,
            "temporal_orientation": temporal_orientation,
            "predicate_context": predicate_context,
        }

    def _get_temporal_predicate_context(
        self,
        document: Document,
        annotation: Annotation,
    ) -> dict[str, Any] | None:
        stanza = document.metadata.get("stanza")

        if not isinstance(stanza, dict):
            return None

        sentences = stanza.get("sentences")

        if not isinstance(sentences, list):
            return None

        for sentence in sentences:
            words = sentence.get("words")

            if not isinstance(words, list):
                continue

            annotation_words = [
                word
                for word in words
                if self._spans_overlap(
                    annotation.start,
                    annotation.end,
                    word.get("start"),
                    word.get("end"),
                )
            ]

            if not annotation_words:
                continue

            words_by_id = {
                word.get("id"): word
                for word in words
                if isinstance(word.get("id"), int)
            }

            contexts: list[
                tuple[int, dict[str, Any]]
            ] = []

            for word in annotation_words:
                result = self._walk_to_local_predicate(
                    word,
                    words_by_id,
                )

                if result is not None:
                    contexts.append(result)

            if not contexts:
                continue

            contexts.sort(key=lambda item: item[0])

            distance, predicate_word = contexts[0]

            auxiliaries = self._get_auxiliaries(
                predicate_word,
                words,
            )

            return {
                "sentence_id": sentence.get("id"),
                "distance": distance,
                "predicate": self._word_info(predicate_word),
                "auxiliaries": [
                    self._word_info(auxiliary)
                    for auxiliary in auxiliaries
                ],
            }

        return None

    def _walk_to_local_predicate(
        self,
        word: dict[str, Any],
        words_by_id: dict[int, dict[str, Any]],
    ) -> tuple[int, dict[str, Any]] | None:
        current = word
        visited: set[int] = set()
        distance = 0

        while True:
            word_id = current.get("id")

            if not isinstance(word_id, int):
                return None

            if word_id in visited:
                return None

            visited.add(word_id)

            if self._is_predicative_word(current):
                return distance, current

            head_id = current.get("head")

            if not isinstance(head_id, int) or head_id == 0:
                return None

            head = words_by_id.get(head_id)

            if head is None:
                return None

            current = head
            distance += 1

    def _is_predicative_word(
        self,
        word: dict[str, Any],
    ) -> bool:
        upos = word.get("upos")

        if upos in {"VERB", "AUX"}:
            return True

        # Participial predicates may be tagged as ADJ by Stanza.
        # They form a local predicative boundary and prevent temporal
        # evidence from leaking in from a higher clause.
        if upos == "ADJ":
            return (
                self._extract_feature(
                    word.get("feats"),
                    "VerbForm",
                )
                == "Part"
            )

        return False

    @staticmethod
    def _get_auxiliaries(
        predicate: dict[str, Any],
        words: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        predicate_id = predicate.get("id")

        if not isinstance(predicate_id, int):
            return []

        auxiliaries = [
            word
            for word in words
            if word.get("head") == predicate_id
            and isinstance(word.get("deprel"), str)
            and word["deprel"].startswith("aux")
        ]

        auxiliaries.sort(
            key=lambda word: (
                word.get("start")
                if isinstance(word.get("start"), int)
                else 0
            )
        )

        return auxiliaries

    def _classify_temporal_orientation(
        self,
        context: dict[str, Any] | None,
    ) -> str:
        if context is None:
            return "UNKNOWN"

        predicate = context.get("predicate")

        if not isinstance(predicate, dict):
            return "UNKNOWN"

        predicate_orientation = self._word_temporal_orientation(
            predicate,
        )

        if predicate_orientation in {"PAST", "FUTURE"}:
            return predicate_orientation

        auxiliaries = context.get("auxiliaries", [])

        if not isinstance(auxiliaries, list):
            return "UNKNOWN"

        orientations = {
            self._word_temporal_orientation(auxiliary)
            for auxiliary in auxiliaries
        }

        orientations.discard("UNKNOWN")

        # Only accept auxiliary evidence when it is unambiguous.
        if orientations == {"PAST"}:
            return "PAST"

        if orientations == {"FUTURE"}:
            return "FUTURE"

        return "UNKNOWN"

    def _word_temporal_orientation(
        self,
        word: dict[str, Any],
    ) -> str:
        feats = word.get("feats")

        tense = self._extract_feature(
            feats,
            "Tense",
        )

        verb_form = self._extract_feature(
            feats,
            "VerbForm",
        )

        # Future morphology provides explicit future evidence.
        if tense == "Fut":
            return "FUTURE"

        # Past and imperfect morphology provide explicit past evidence.
        #
        # Stanza uses Tense=Imp for forms such as "había".
        if tense in {"Past", "Imp"}:
            return "PAST"

        # Present, infinitive and other underspecified forms are not
        # interpreted as temporal orientation.
        if tense == "Pres":
            return "UNKNOWN"

        if verb_form in {"Inf", "Ger"}:
            return "UNKNOWN"

        return "UNKNOWN"

    def _word_info(
        self,
        word: dict[str, Any],
    ) -> dict[str, Any]:
        feats = word.get("feats")

        return {
            "text": word.get("text"),
            "lemma": word.get("lemma"),
            "upos": word.get("upos"),
            "deprel": word.get("deprel"),
            "feats": feats,
            "tense": self._extract_feature(
                feats,
                "Tense",
            ),
            "verb_form": self._extract_feature(
                feats,
                "VerbForm",
            ),
            "word_id": word.get("id"),
        }

    @staticmethod
    def _extract_feature(
        feats: str | None,
        feature: str,
    ) -> str | None:
        if not isinstance(feats, str):
            return None

        prefix = f"{feature}="

        for item in feats.split("|"):
            if item.startswith(prefix):
                return item[len(prefix):]

        return None

    def _extract_day_month_without_year(
        self,
        annotation: Annotation,
    ) -> tuple[int, int] | None:
        normalized = annotation.metadata.get("normalized")

        if not isinstance(normalized, str):
            return None

        try:
            resolved = pendulum.parse(normalized)
        except (ValueError, TypeError):
            return None

        if str(resolved.year) in annotation.text:
            return None

        raw_value = annotation.metadata.get("raw_value")

        if not isinstance(raw_value, dict):
            return None

        grain = annotation.metadata.get("grain")

        if grain != "day":
            return None

        return resolved.day, resolved.month

    @staticmethod
    def _spans_overlap(
        start_a: int,
        end_a: int,
        start_b: Any,
        end_b: Any,
    ) -> bool:
        if not isinstance(start_b, int):
            return False

        if not isinstance(end_b, int):
            return False

        return start_a < end_b and start_b < end_a

    @staticmethod
    def _preserve_time_and_timezone(
        resolved: pendulum.DateTime,
        candidate: pendulum.DateTime,
    ) -> str:
        corrected = candidate.replace(
            hour=resolved.hour,
            minute=resolved.minute,
            second=resolved.second,
            microsecond=resolved.microsecond,
        )

        return corrected.to_iso8601_string()

    def _resolve_reference_datetime(
        self,
        document: Document,
    ) -> pendulum.DateTime | None:
        value = self._get_metadata_value(
            document.metadata,
            self.reference_datetime_metadata_key,
        )

        if value is None:
            return None

        return self._parse_datetime(value)

    @staticmethod
    def _get_metadata_value(
        metadata: dict,
        dotted_key: str,
    ):
        current = metadata

        for part in dotted_key.split("."):
            if not isinstance(current, dict):
                return None

            current = current.get(part)

            if current is None:
                return None

        return current

    @staticmethod
    def _parse_datetime(
        value,
    ) -> pendulum.DateTime | None:
        if isinstance(value, pendulum.DateTime):
            return value

        if isinstance(value, datetime):
            return pendulum.instance(value)

        if isinstance(value, str):
            try:
                return pendulum.parse(value)
            except (ValueError, TypeError):
                return None

        return None

    def _refine_weekday(
        self,
        document: Document,
        annotation: Annotation,
        reference_datetime,
    ) -> None:
        if annotation.label != "DATE":
            return

        if annotation.metadata.get("grain") != "day":
            return

        weekday = self._get_annotation_weekday(
            document,
            annotation,
        )
        if weekday is None:
            return

        normalized = annotation.metadata.get("normalized")
        if not isinstance(normalized, str):
            return

        resolved = self._parse_datetime(normalized)
        if resolved is None:
            return

        predicate_context = self._get_temporal_predicate_context(
            document,
            annotation,
        )
        if predicate_context is None:
            return

        orientation = self._classify_temporal_orientation(
            predicate_context,
        )

        if orientation == "UNKNOWN":
            return

        reference_weekday = reference_datetime.day_of_week

        if orientation == "PAST":
            days_back = (
                reference_weekday - weekday
            ) % 7

            candidate = reference_datetime.subtract(
                days=days_back,
            ).start_of("day")

            direction = "previous_or_same"

        elif orientation == "FUTURE":
            days_forward = (
                weekday - reference_weekday
            ) % 7

            # Future means strictly future. If today is the
            # requested weekday, choose the following occurrence.
            if days_forward == 0:
                days_forward = 7

            candidate = reference_datetime.add(
                days=days_forward,
            ).start_of("day")

            direction = "next"

        else:
            return

        resolved_date = resolved.date()
        candidate_date = candidate.date()

        if resolved_date == candidate_date:
            return

        previous_normalized = normalized

        annotation.metadata["normalized"] = (
            self._preserve_time_and_timezone(
                resolved,
                candidate,
            )
        )

        annotation.metadata["context_resolution"] = {
            "rule": "weekday_by_predicate_orientation",
            "previous_normalized": previous_normalized,
            "reference_datetime": (
                reference_datetime.to_iso8601_string()
            ),
            "temporal_orientation": orientation,
            "candidate_direction": direction,
            "distance_days": abs(
                (candidate_date - reference_datetime.date()).days
            ),
            "predicate_context": predicate_context,
        }


    def _get_annotation_weekday(
        self,
        document: Document,
        annotation: Annotation,
    ) -> int | None:
        stanza = document.metadata.get("stanza")
        if not isinstance(stanza, dict):
            return None

        sentences = stanza.get("sentences")
        if not isinstance(sentences, list):
            return None

        matches: set[int] = set()

        for sentence in sentences:
            words = sentence.get("words", [])

            for word in words:
                start = word.get("start")
                end = word.get("end")

                if not isinstance(start, int):
                    continue

                if not isinstance(end, int):
                    continue

                if not self._spans_overlap(
                    annotation.start,
                    annotation.end,
                    start,
                    end,
                ):
                    continue

                lemma = str(
                    word.get("lemma") or word.get("text") or ""
                ).lower()

                weekday = self.rules.weekdays.get(lemma)

                if weekday is not None:
                    matches.add(weekday)

        if len(matches) != 1:
            return None

        return next(iter(matches))

    def _refine_time_from_contextual_date(
        self,
        document: Document,
        annotation: Annotation,
    ) -> None:
        if annotation.label != "TIME":
            return

        if annotation.metadata.get("date_resolved") is not False:
            return

        normalized = annotation.metadata.get("normalized")

        if not isinstance(normalized, str):
            return

        clock_time = self._parse_clock_time(normalized)

        if clock_time is None:
            return

        time_context = self._get_temporal_predicate_context(
            document,
            annotation,
        )

        time_predicate_key = self._predicate_context_key(time_context)

        if time_predicate_key is None:
            return

        candidates: list[
            tuple[Annotation, pendulum.DateTime, dict[str, Any]]
        ] = []

        for candidate_annotation in document.annotations:
            if candidate_annotation is annotation:
                continue

            if candidate_annotation.layer != "temporal":
                continue

            if candidate_annotation.label != "DATE":
                continue

            candidate_normalized = candidate_annotation.metadata.get(
                "normalized"
            )

            if not isinstance(candidate_normalized, str):
                continue

            candidate_date = self._parse_datetime(candidate_normalized)

            if candidate_date is None:
                continue

            candidate_context = self._get_temporal_predicate_context(
                document,
                candidate_annotation,
            )

            candidate_predicate_key = self._predicate_context_key(
                candidate_context
            )

            if candidate_predicate_key != time_predicate_key:
                continue

            candidates.append(
                (
                    candidate_annotation,
                    candidate_date,
                    candidate_context,
                )
            )

        # Ambiguous contextual evidence must not modify the annotation.
        if len(candidates) != 1:
            return

        (
            date_annotation,
            contextual_date,
            predicate_context,
        ) = candidates[0]

        previous_normalized = normalized

        resolved = contextual_date.replace(
            hour=clock_time[0],
            minute=clock_time[1],
            second=clock_time[2],
            microsecond=0,
        )

        annotation.metadata["normalized"] = (
            resolved.to_iso8601_string()
        )
        annotation.metadata["date_resolved"] = True

        annotation.metadata["context_resolution"] = {
            "rule": "time_from_date_same_predicate",
            "previous_normalized": previous_normalized,
            "date_annotation": {
                "start": date_annotation.start,
                "end": date_annotation.end,
                "text": date_annotation.text,
                "normalized": date_annotation.metadata.get(
                    "normalized"
                ),
            },
            "predicate_context": predicate_context,
        }

    @staticmethod
    def _predicate_context_key(
        context: dict[str, Any] | None,
    ) -> tuple[Any, int] | None:
        if context is None:
            return None

        sentence_id = context.get("sentence_id")
        predicate = context.get("predicate")

        if not isinstance(predicate, dict):
            return None

        word_id = predicate.get("word_id")

        if not isinstance(word_id, int):
            return None

        return sentence_id, word_id


    @staticmethod
    def _parse_clock_time(
        value: str,
    ) -> tuple[int, int, int] | None:
        parts = value.split(":")

        if len(parts) not in {2, 3}:
            return None

        try:
            hour = int(parts[0])
            minute = int(parts[1])
            second = int(parts[2]) if len(parts) == 3 else 0
        except ValueError:
            return None

        if not 0 <= hour <= 23:
            return None

        if not 0 <= minute <= 59:
            return None

        if not 0 <= second <= 59:
            return None

        return hour, minute, second

    def _refine_month_without_year(
        self,
        document: Document,
        annotation: Annotation,
        reference_datetime: pendulum.DateTime,
    ) -> None:
        if annotation.label != "DATE":
            return

        if annotation.metadata.get("grain") != "month":
            return

        if self._has_explicit_year(annotation):
            return        

        normalized = annotation.metadata.get("normalized")

        if not isinstance(normalized, str):
            return

        resolved = self._parse_datetime(normalized)

        if resolved is None:
            return

        # This rule only corrects Duckling resolutions that point
        # to a future year.
        if resolved.year <= reference_datetime.year:
            return

        # A month-only expression can only be moved to the reference
        # year if that month has already started by publication time.
        if resolved.month > reference_datetime.month:
            return

        predicate_context = self._get_temporal_predicate_context(
            document,
            annotation,
        )

        if predicate_context is None:
            return

        temporal_orientation = self._classify_temporal_orientation(
            predicate_context,
        )

        if temporal_orientation != "PAST":
            return

        candidate = resolved.replace(
            year=reference_datetime.year,
        )

        # Do not turn the expression into a future date within the
        # reference year.
        if candidate > reference_datetime:
            return

        previous_normalized = normalized

        annotation.metadata["normalized"] = (
            candidate.to_iso8601_string()
        )

        annotation.metadata["context_resolution"] = {
            "rule": "month_by_predicate_orientation",
            "previous_normalized": previous_normalized,
            "reference_datetime": (
                reference_datetime.to_iso8601_string()
            ),
            "temporal_orientation": temporal_orientation,
            "distance_months": (
                (reference_datetime.year - candidate.year) * 12
                + reference_datetime.month
                - candidate.month
            ),
            "predicate_context": predicate_context,
        }

    @staticmethod
    def _has_explicit_year(annotation: Annotation) -> bool:
        return bool(
            re.search(
                r"(?<!\d)(?:1[0-9]{3}|2[0-9]{3})(?!\d)",
                annotation.text,
            )
        )

    def _refine_relative_time_as_duration(
        self,
        document: Document,
        annotation: Annotation,
        reference_datetime: pendulum.DateTime,
    ) -> None:
        if annotation.label != "DATE":
            return

        if annotation.metadata.get("duckling_dim") != "time":
            return

        body = annotation.metadata.get("duckling_body")
        if not isinstance(body, str):
            return

        if not body.lower().startswith("en "):
            return

        unit_info = self._get_quantified_temporal_unit(
            document,
            annotation,
        )
        if unit_info is None:
            return

        unit, seconds_per_unit = unit_info

        previous_normalized = annotation.metadata.get("normalized")

        resolved_datetime = self._parse_datetime(previous_normalized)
        if resolved_datetime is None:
            return

        duration_seconds = (
            resolved_datetime - reference_datetime
        ).total_seconds()

        if duration_seconds <= 0:
            return

        duration_value = duration_seconds / seconds_per_unit

        if duration_seconds.is_integer():
            duration_seconds = int(duration_seconds)

        if duration_value.is_integer():
            duration_value = int(duration_value)

        predicate_context = self._get_temporal_predicate_context(
            document,
            annotation,
        )
        if predicate_context is None:
            return

        temporal_orientation = self._classify_temporal_orientation(
            predicate_context,
        )
        if temporal_orientation != "PAST":
            return

        previous_normalized = annotation.metadata.get("normalized")

        annotation.label = "DURATION"
        annotation.subtype = "duration"

        annotation.metadata["normalized"] = duration_value
        annotation.metadata["duration"] = {
            "unit": unit,
            "value": duration_value,
            "normalized": {
                "unit": "second",
                "value": duration_seconds,
            },
        }
        annotation.metadata["resolved_from"] = "DATE"
        annotation.metadata["refined_by"] = "temporal-context"
        annotation.metadata["context_resolution"] = {
            "rule": "relative_time_as_elapsed_duration",
            "previous_normalized": previous_normalized,
            "reference_datetime": reference_datetime.to_iso8601_string(),
            "temporal_orientation": temporal_orientation,
            "predicate_context": predicate_context,
        }


    def _get_quantified_temporal_unit(
        self,
        document: Document,
        annotation: Annotation,
    ) -> tuple[str, int] | None:
        stanza = document.metadata.get("stanza")
        if not isinstance(stanza, dict):
            return None

        sentences = stanza.get("sentences")
        if not isinstance(sentences, list):
            return None

        for sentence in sentences:
            words = sentence.get("words")
            if not isinstance(words, list):
                continue

            words_by_id = {
                word.get("id"): word
                for word in words
                if isinstance(word, dict)
                and isinstance(word.get("id"), int)
            }

            for word in words:
                if not isinstance(word, dict):
                    continue

                start = word.get("start")
                end = word.get("end")

                if not isinstance(start, int) or not isinstance(end, int):
                    continue

                if start < annotation.start or end > annotation.end:
                    continue

                if word.get("upos") != "NOUN":
                    continue

                if word.get("deprel") != "obl":
                    continue

                word_id = word.get("id")
                if not isinstance(word_id, int):
                    continue

                has_numeric_modifier = any(
                    child.get("head") == word_id
                    and child.get("deprel") == "nummod"
                    and child.get("upos") == "NUM"
                    for child in words_by_id.values()
                )
                if not has_numeric_modifier:
                    continue

                lemma = word.get("lemma")
                if not isinstance(lemma, str):
                    continue

                unit_info = self.rules.duration_units.get(
                    lemma.lower(),
                )
                if unit_info is not None:
                    return unit_info

        return None