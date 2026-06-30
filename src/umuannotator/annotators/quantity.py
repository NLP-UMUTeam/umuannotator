from __future__ import annotations

from umuannotator.annotators.duckling import DucklingAnnotator
from umuannotator.annotators.overlap import resolve_layer_overlaps
from umuannotator.annotators.stanza_utils import find_stanza_token
from umuannotator.document.model import Annotation, Document
from umuannotator.lang.quantity import get_quantity_rules


class QuantityAnnotator(DucklingAnnotator):
    def __init__(
        self,
        language: str = "es",
        locale: str | None = None,
        timezone: str = "Europe/Madrid",
        layer: str = "cantidades",
    ):
        self.rules = get_quantity_rules(language)

        super().__init__(
            dimensions=[
                "number",
                "amount-of-money",
                "distance",
                "volume",
                "temperature",
                "ordinal",
                "quantity",
            ],
            language=language,
            locale=locale,
            timezone=timezone,
            layer=layer,
            source="duckling-quantity",
        )

    def annotate(self, document: Document) -> Document:
        super().annotate(document)

        document.annotations = resolve_layer_overlaps(
            document.annotations,
            layer=self.layer,
        )

        return document

    def result_to_annotation(
        self,
        document: Document,
        result: dict,
    ) -> Annotation | None:
        annotation = super().result_to_annotation(document, result)

        if annotation is None:
            return None

        if self._is_false_positive_determiner(annotation, document):
            return None

        annotation.type = "quantity"
        annotation.label = self._quantity_label(result)

        annotation.metadata["normalized"] = self._normalized_value(result)
        annotation.metadata["raw_value"] = result.get("value", {})
        annotation.metadata["duckling_dim"] = result.get("dim")
        annotation.metadata["duckling_body"] = result.get("body")
        annotation.metadata["unit"] = self._unit(result)

        self._expand_number_multiplier(annotation, document)

        stanza_token = find_stanza_token(
            document,
            start=annotation.start,
            end=annotation.end,
        )

        if stanza_token is not None:
            annotation.metadata["stanza"] = {
                "lemma": stanza_token.get("lemma"),
                "upos": stanza_token.get("upos"),
                "xpos": stanza_token.get("xpos"),
                "feats": stanza_token.get("feats"),
            }

        return annotation

    def _quantity_label(self, result: dict) -> str:
        dim = result.get("dim")

        if dim == "number":
            return "NUMBER"

        if dim == "amount-of-money":
            return "MONEY"

        if dim == "distance":
            return "DISTANCE"

        if dim == "volume":
            return "VOLUME"

        if dim == "temperature":
            return "TEMPERATURE"

        if dim == "ordinal":
            return "ORDINAL"

        if dim == "quantity":
            return "QUANTITY"

        return "QUANTITY"

    def _normalized_value(self, result: dict):
        value = result.get("value", {})

        if isinstance(value, dict):
            return (
                value.get("value")
                or value.get("amount")
                or value.get("normalized", {}).get("value")
            )

        return value

    def _unit(self, result: dict) -> str | None:
        value = result.get("value", {})

        if not isinstance(value, dict):
            return None

        normalized = value.get("normalized", {})

        if isinstance(normalized, dict):
            return value.get("unit") or normalized.get("unit")

        return value.get("unit")

    def _is_false_positive_determiner(
        self,
        annotation: Annotation,
        document: Document,
    ) -> bool:
        surface = annotation.text.lower().strip()

        if surface not in self.rules.determiner_number_words:
            return False

        token = find_stanza_token(
            document,
            start=annotation.start,
            end=annotation.end,
        )

        if token is None:
            return False

        return token.get("upos") == "DET"

    def _expand_number_multiplier(
        self,
        annotation: Annotation,
        document: Document,
    ) -> None:
        if annotation.label != "NUMBER":
            return

        if self.rules.multiplier_after_number_re is None:
            return

        tail = document.text[annotation.end:]
        match = self.rules.multiplier_after_number_re.match(tail)

        if not match:
            return

        multiplier_text = match.group(1)
        multiplier_key = multiplier_text.lower()
        multiplier_value = self.rules.multipliers.get(multiplier_key)

        extension_end = annotation.end + match.end()

        annotation.end = extension_end
        annotation.text = document.text[annotation.start:annotation.end]
        annotation.label = "QUANTITY"
        annotation.subtype = "multiplier"

        annotation.metadata["multiplier"] = multiplier_key
        annotation.metadata["multiplier_value"] = multiplier_value

        normalized = annotation.metadata.get("normalized")

        if normalized is not None and multiplier_value is not None:
            try:
                annotation.metadata["normalized"] = (
                    float(normalized) * multiplier_value
                )
            except (TypeError, ValueError):
                pass