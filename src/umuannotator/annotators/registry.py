# src/umuannotator/annotators/registry.py

from typing import Any

from umuannotator.document.model import Document


class AnnotatorFactory:
    def create(
        self,
        name: str,
        *,
        language: str = "es",
        ontology_path: str | None = None,
        **kwargs: Any,
    ):
        if name == "ontology":
            if ontology_path is None:
                raise ValueError("ontology annotator requires ontology_path")

            from umuannotator.annotators.ontology import OntologyAnnotator
            from umuannotator.ontology.loader import load_ontology
            from umuannotator.ontology.index import build_index

            graph = load_ontology(ontology_path)
            concepts = build_index(graph)

            return OntologyAnnotator(
                concepts=concepts,
                source=ontology_path,
            )

        if name == "stanza-ner":
            from umuannotator.annotators.stanza_ner import StanzaNERAnnotator

            return StanzaNERAnnotator(language=language)

        if name == "dbpedia":
            from umuannotator.annotators.dbpedia import DBpediaSpotlightAnnotator

            return DBpediaSpotlightAnnotator(language=language)

        if name == "regex":
            from umuannotator.annotators.regex import RegexAnnotator

            source = kwargs.get("source")
            layer = kwargs.get("layer", "regex")

            if source is None:
                raise ValueError("regex annotator requires source")

            return RegexAnnotator(
                source=source,
                layer=layer,
            )

        if name == "duckling":
            from umuannotator.annotators.duckling import DucklingAnnotator

            dimensions = kwargs.get("dimensions")
            layer = kwargs.get("layer", "duckling")
            locale = kwargs.get("locale")
            timezone = kwargs.get("timezone", "Europe/Madrid")

            if not dimensions:
                raise ValueError("duckling annotator requires dimensions")

            return DucklingAnnotator(
                dimensions=dimensions,
                language=language,
                locale=locale,
                timezone=timezone,
                layer=layer,
            )

        if name == "temporal":
            from umuannotator.annotators.temporal import TemporalAnnotator

            return TemporalAnnotator(
                language=language,
                locale=kwargs.get("locale"),
                timezone=kwargs.get("timezone", "Europe/Madrid"),
                layer=kwargs.get("layer", "temporal"),
            )

        raise ValueError(f"Unknown annotator: {name}")


def build_annotators(
    names: list,
    *,
    language: str = "es",
    ontology_path: str | None = None,
):
    factory = AnnotatorFactory()

    annotators = []

    for item in names:
        if isinstance(item, str):
            name = item
            params = {}
        else:
            name = item["name"]
            params = {
                key: value
                for key, value in item.items()
                if key != "name"
            }

        annotators.append(
            factory.create(
                name,
                language=language,
                ontology_path=ontology_path,
                **params,
            )
        )

    return annotators