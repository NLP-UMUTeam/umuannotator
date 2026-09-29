from __future__ import annotations

from datetime import date, datetime
from typing import Any

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
        reference_datetime_metadata_key: str | None = None,
    ):
        self.dimensions_names = dimensions
        self.language = language
        self.locale_code = locale or self._locale_from_language(language)
        self.timezone = timezone
        self.layer = layer
        self.source = source
        self.reference_datetime_metadata_key = (
            reference_datetime_metadata_key
        )

        self.time_zones = load_time_zones(
            "/usr/share/zoneinfo"
        )
        self.dimensions = parse_dimensions(
            dimensions
        )

    def annotate(
        self,
        document: Document,
    ) -> Document:
        (
            reference_datetime,
            reference_source,
        ) = self._resolve_reference_datetime(
            document
        )

        context = self._build_context(
            reference_datetime
        )

        results = parse(
            document.text,
            context,
            self.dimensions,
            False,
        )

        for result in results:
            annotation = self.result_to_annotation(
                document,
                result,
            )

            if annotation is None:
                continue

            if reference_source is not None:
                annotation.metadata[
                    "reference_datetime"
                ] = reference_datetime.isoformat()

                annotation.metadata[
                    "reference_datetime_source"
                ] = reference_source

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
                "value": result.get(
                    "value",
                    {},
                ),
                "body": surface,
                "locale": self.locale_code,
                "timezone": self.timezone,
            },
        )

    def _resolve_reference_datetime(
        self,
        document: Document,
    ) -> tuple[pendulum.DateTime, str | None]:
        if self.reference_datetime_metadata_key:
            raw_value = self._get_metadata_value(
                document.metadata,
                self.reference_datetime_metadata_key,
            )

            if raw_value is not None:
                reference_datetime = (
                    self._parse_reference_datetime(
                        raw_value
                    )
                )

                return (
                    reference_datetime,
                    self.reference_datetime_metadata_key,
                )

        return (
            pendulum.now(
                self.timezone
            ).replace(
                microsecond=0
            ),
            None,
        )

    def _parse_reference_datetime(
        self,
        value: Any,
    ) -> pendulum.DateTime:
        if isinstance(
            value,
            pendulum.DateTime,
        ):
            return value.in_timezone(
                self.timezone
            )

        if isinstance(
            value,
            datetime,
        ):
            if value.tzinfo is None:
                return pendulum.datetime(
                    value.year,
                    value.month,
                    value.day,
                    value.hour,
                    value.minute,
                    value.second,
                    value.microsecond,
                    tz=self.timezone,
                )

            return pendulum.instance(
                value
            ).in_timezone(
                self.timezone
            )

        if isinstance(
            value,
            date,
        ):
            return pendulum.datetime(
                value.year,
                value.month,
                value.day,
                tz=self.timezone,
            )

        if isinstance(
            value,
            str,
        ):
            stripped = value.strip()

            if not stripped:
                raise ValueError(
                    "Reference datetime cannot be empty"
                )

            parsed = pendulum.parse(
                stripped,
                tz=self.timezone,
            )

            return parsed.in_timezone(
                self.timezone
            )

        raise ValueError(
            "Unsupported reference datetime value: "
            f"{value!r}"
        )

    @staticmethod
    def _get_metadata_value(
        metadata: dict[str, Any],
        path: str,
    ) -> Any:
        current: Any = metadata

        for part in path.split("."):
            if not isinstance(
                current,
                dict,
            ):
                return None

            if part not in current:
                return None

            current = current[part]

        return current

    def _build_context(
        self,
        reference_datetime: pendulum.DateTime,
    ) -> Context:
        ref_time = parse_ref_time(
            self.time_zones,
            self.timezone,
            reference_datetime.int_timestamp,
        )

        lang = parse_lang(
            self._duckling_language(
                self.language
            )
        )

        default_locale = default_locale_lang(
            lang
        )

        locale = parse_locale(
            self.locale_code,
            default_locale,
        )

        return Context(
            ref_time,
            locale,
        )

    def _label_for(
        self,
        result: dict,
    ) -> str:
        dim = result.get(
            "dim",
            "duckling",
        )

        return dim.upper().replace(
            "-",
            "_",
        )

    def _locale_from_language(
        self,
        language: str,
    ) -> str:
        return {
            "es": "ES_ES",
            "en": "EN_US",
        }.get(
            language,
            language.upper(),
        )

    def _duckling_language(
        self,
        language: str,
    ) -> str:
        return {
            "es": "ES",
            "en": "EN",
        }.get(
            language,
            language.upper(),
        )