from __future__ import annotations

from umuannotator.annotators.duckling import DucklingAnnotator
from umuannotator.document.model import Annotation, Document


BAD_STARTS = {"a", "en", "de", "por", "para", "con", "sin"}
BAD_SINGLE_WORDS = {"una", "un", "uno"}


def is_bad_temporal_surface(surface: str) -> bool:
    words = surface.lower().strip().split()

    if not words:
        return True

    if len(words) == 1 and words[0] in BAD_SINGLE_WORDS:
        return True

    if len(words) == 2 and words[0] in BAD_STARTS and words[1] in BAD_SINGLE_WORDS:
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

        if is_bad_temporal_surface(annotation.text):
            return None

        annotation.type = "temporal"
        annotation.label = self._temporal_label(result)

        annotation.metadata["normalized"] = self._normalized_value(result)
        annotation.metadata["raw_value"] = result.get("value", {})

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