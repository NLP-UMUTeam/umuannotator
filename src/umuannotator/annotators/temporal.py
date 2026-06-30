from __future__ import annotations

from umuannotator.annotators.duckling import DucklingAnnotator
from umuannotator.annotators.stanza_utils import find_stanza_entity_containing
from umuannotator.document.model import Annotation, Document
from umuannotator.lang.temporal import TemporalLanguageRules, get_temporal_rules


def is_bad_temporal_surface(
    surface: str,
    *,
    dim: str | None = None,
    grain: str | None = None,
    rules: TemporalLanguageRules | None = None,
) -> bool:
    rules = rules or get_temporal_rules("es")

    normalized = surface.lower().strip()
    words = normalized.split()

    if not words:
        return True

    if normalized in rules.bad_single_words:
        return True

    if normalized in rules.bad_year_surfaces and grain == "year":
        return True

    if len(words) == 2 and words[0] in rules.bad_starts and words[1] in rules.bad_single_words:
        return True

    if (
        len(words) == 2
        and words[0] == "a"
        and words[1] in rules.bad_prepositional_time_words
    ):
        return True

    if normalized.startswith("un ") and grain == "minute":
        return True

    if dim == "duration" and len(words) == 1 and words[0].isdigit():
        return True

    return False


class TemporalAnnotator(DucklingAnnotator):
    def __init__(
        self,
        language: str = "es",
        locale: str | None = None,
        timezone: str = "Europe/Madrid",
        layer: str = "temporal",
    ):
        self.rules = get_temporal_rules(language)

        super().__init__(
            dimensions=["time", "time-grain", "duration"],
            language=language,
            locale=locale,
            timezone=timezone,
            layer=layer,
            source="duckling-temporal",
        )

    def result_to_annotation(
        self,
        document: Document,
        result: dict,
    ) -> Annotation | None:
        annotation = super().result_to_annotation(document, result)

        if annotation is None:
            return None

        grain = self._grain(result)

        if is_bad_temporal_surface(
            annotation.text,
            dim=result.get("dim"),
            grain=grain,
            rules=self.rules,
        ):
            return None

        if self._is_false_positive_person_name(annotation, document):
            return None

        annotation.type = "temporal"
        annotation.label = self._temporal_label(result)

        annotation.metadata["normalized"] = self._normalized_value(result)
        annotation.metadata["grain"] = grain
        annotation.metadata["raw_value"] = result.get("value", {})
        annotation.metadata["duckling_dim"] = result.get("dim")
        annotation.metadata["duckling_body"] = result.get("body")

        return annotation

    def _temporal_label(self, result: dict) -> str:
        dim = result.get("dim")

        if dim == "time":
            return "DATE"

        if dim == "duration":
            return "DURATION"

        if dim == "time-grain":
            return "TIME_GRAIN"

        return "TEMPORAL"

    def _normalized_value(self, result: dict):
        value = result.get("value", {})

        if isinstance(value, dict):
            return (
                value.get("value")
                or value.get("from", {}).get("value")
                or value.get("to", {}).get("value")
            )

        return value

    def _grain(self, result: dict) -> str | None:
        value = result.get("value", {})

        if isinstance(value, dict):
            return value.get("grain")

        return None

    def _is_false_positive_person_name(
        self,
        annotation: Annotation,
        document: Document,
    ) -> bool:
        surface = annotation.text.lower().strip()

        if surface not in self.rules.person_name_month_words:
            return False

        entity = find_stanza_entity_containing(
            document,
            start=annotation.start,
            end=annotation.end,
        )

        if entity is None:
            return False

        entity_type = entity.get("type") or entity.get("label")

        return entity_type in {"PER", "PERSON"}