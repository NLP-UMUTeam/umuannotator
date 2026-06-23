from __future__ import annotations

import pendulum

from duckling import (
    Context,
    default_locale_lang,
    load_time_zones,
    parse,
    parse_dimensions,
    parse_lang,
    parse_locale,
    parse_ref_time,
)

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

class TemporalAnnotator:
    layer = "temporal"

    def __init__(
        self,
        language: str = "es",
        locale: str | None = None,
        timezone: str = "Europe/Madrid",
    ):
        self.language = language
        self.locale_code = locale or self._locale_from_language(language)
        self.timezone = timezone

        self.time_zones = load_time_zones("/usr/share/zoneinfo")
        self.dimensions = parse_dimensions(["time", "time-grain", "duration"])

    def annotate(self, document: Document) -> Document:
        context = self._build_context()

        results = parse(
            document.text,
            context,
            self.dimensions,
            False,
        )

        for result in results:
            start = result.get("start")
            end = result.get("end")

            if start is None or end is None:
                continue

            value = result.get("value", {})
            body = result.get("body") or document.text[start:end]

            surface = document.text[start:end].strip()
            surface_lower = surface.lower()

            if is_bad_temporal_surface(surface):
                continue

            document.add_annotation(
                Annotation(
                    start=start,
                    end=end,
                    text=document.text[start:end],
                    label=self._label_for(result),
                    layer=self.layer,
                    source="duckling",
                    type="temporal",
                    subtype=result.get("dim"),
                    metadata={
                        "body": body,
                        "dim": result.get("dim"),
                        "value": value,
                        "locale": self.locale_code,
                        "timezone": self.timezone,
                    },
                )
            )

        return document

    def _build_context(self) -> Context:
        now = pendulum.now(self.timezone).replace(microsecond=0)

        ref_time = parse_ref_time(
            self.time_zones,
            self.timezone,
            now.int_timestamp,
        )

        lang = parse_lang(self._duckling_language(self.language))
        default_locale = default_locale_lang(lang)
        locale = parse_locale(self.locale_code, default_locale)

        return Context(ref_time, locale)

    def _label_for(self, result: dict) -> str:
        dim = result.get("dim")

        if dim == "time":
            return "DATE"

        if dim == "duration":
            return "DURATION"

        if dim == "time-grain":
            return "TIME_GRAIN"

        return "TEMPORAL"

    def _locale_from_language(self, language: str) -> str:
        return {
            "es": "ES_ES",
            "en": "EN_US",
        }.get(language, language.upper())

    def _duckling_language(self, language: str) -> str:
        return {
            "es": "ES",
            "en": "EN",
        }.get(language, language.upper())