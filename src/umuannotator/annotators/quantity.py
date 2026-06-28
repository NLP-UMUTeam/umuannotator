from __future__ import annotations

from umuannotator.annotators.duckling import DucklingAnnotator
from umuannotator.document.model import Annotation, Document


DET_NUMBER_WORDS = {"un", "una", "uno"}


class QuantityAnnotator(DucklingAnnotator):
    def __init__(
        self,
        language: str = "es",
        locale: str | None = None,
        timezone: str = "Europe/Madrid",
        layer: str = "cantidades",
    ):
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

        stanza_token = self._find_stanza_token(annotation, document)
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

    def _is_false_positive_determiner(
        self,
        annotation: Annotation,
        document: Document,
    ) -> bool:
        surface = annotation.text.lower().strip()

        if surface not in DET_NUMBER_WORDS:
            return False

        token = self._find_stanza_token(annotation, document)

        if token is None:
            return False

        return token.get("upos") == "DET"

    def _find_stanza_token(
        self,
        annotation: Annotation,
        document: Document,
    ) -> dict | None:
        stanza = document.metadata.get("stanza")

        if not stanza:
            return None

        for token in stanza.get("tokens", []):
            if (
                token.get("start") == annotation.start
                and token.get("end") == annotation.end
            ):
                return token

        return None