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


class DucklingAnnotator:
    def __init__(
        self,
        dimensions: list[str],
        language: str = "es",
        locale: str | None = None,
        timezone: str = "Europe/Madrid",
        layer: str = "duckling",
        source: str = "duckling",
    ):
        self.dimensions_names = dimensions
        self.language = language
        self.locale_code = locale or self._locale_from_language(language)
        self.timezone = timezone
        self.layer = layer
        self.source = source

        self.time_zones = load_time_zones("/usr/share/zoneinfo")
        self.dimensions = parse_dimensions(dimensions)

    def annotate(self, document: Document) -> Document:
        context = self._build_context()

        results = parse(
            document.text,
            context,
            self.dimensions,
            False,
        )

        for result in results:
            annotation = self.result_to_annotation(document, result)

            if annotation is not None:
                document.add_annotation(annotation)

        return document

    def result_to_annotation(
        self,
        document: Document,
        result: dict,
    ) -> Annotation | None:
        start = result.get("start")
        end = result.get("end")

        if start is None or end is None:
            return None

        surface = document.text[start:end]

        return Annotation(
            start=start,
            end=end,
            text=surface,
            label=self._label_for(result),
            layer=self.layer,
            source=self.source,
            type="duckling",
            subtype=result.get("dim"),
            metadata={
                "dim": result.get("dim"),
                "value": result.get("value", {}),
                "body": result.get("body"),
                "locale": self.locale_code,
                "timezone": self.timezone,
            },
        )

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
        dim = result.get("dim", "duckling")
        return dim.upper().replace("-", "_")

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