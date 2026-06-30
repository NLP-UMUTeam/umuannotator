from __future__ import annotations

from umuannotator.annotators.duckling import DucklingAnnotator
from umuannotator.document.model import Annotation, Document
from umuannotator.annotators.stanza_utils import find_stanza_entity_containing


BAD_STARTS = {"a", "en", "de", "del", "por", "para", "con", "sin"}

BAD_SINGLE_WORDS = {
    "una",
    "un",
    "uno",
    "unos",
    "unas",
    "ya",
    "ahora",
    "primero",
    "mar",
}

BAD_PREPOSITIONAL_TIME_WORDS = {
    "una",
    "un",
    "uno",
    "dos",
    "tres",
    "cuatro",
    "cinco",
    "seis",
    "siete",
    "ocho",
    "nueve",
    "diez",
    "once",
    "doce",
}

BAD_YEAR_SURFACES = {
    "mil",
    "1.000",
    "1000",
    "2.000",
}


def is_bad_temporal_surface(
    surface: str,
    *,
    dim: str | None = None,
    grain: str | None = None,
) -> bool:
    normalized = surface.lower().strip()
    words = normalized.split()

    if not words:
        return True

    if normalized in BAD_SINGLE_WORDS:
        return True

    if normalized in BAD_YEAR_SURFACES and grain == "year":
        return True

    if len(words) == 2 and words[0] in BAD_STARTS and words[1] in BAD_SINGLE_WORDS:
        return True

    if (
        len(words) == 2
        and words[0] == "a"
        and words[1] in BAD_PREPOSITIONAL_TIME_WORDS
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

        if surface not in {"julio"}:
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

