from typing import Any
from pathlib import Path

import yaml

class AnnotatorFactory:
    def create(
        self,
        name: str,
        *,
        language: str = "es",
        ontology_path: str | None = None,
        config: dict | None = None,
        **kwargs: Any,
    ):
        if name == "ontology":
            if ontology_path is None:
                raise ValueError("ontology annotator requires ontology_path")

            from umuannotator.annotators.ontology import OntologyAnnotator
            from umuannotator.ontology.loader import load_ontology
            from umuannotator.ontology.index import build_index

            graph = load_ontology(ontology_path)

            concepts = build_index(
                graph,
                config=config,
            )

            ontology_config = (config or {}).get("ontology", {})

            return OntologyAnnotator(
                concepts=concepts,
                source=ontology_path,
                matching_config=ontology_config.get("matching", {}),
            )

        if name == "stanza-ner":
            from umuannotator.annotators.stanza_ner import StanzaNERAnnotator

            return StanzaNERAnnotator(language=language)

        if name == "dbpedia":
            from umuannotator.annotators.dbpedia import DBpediaSpotlightAnnotator

            return DBpediaSpotlightAnnotator(language=language)

        if name == "pattern":
            from umuannotator.annotators.pattern import PatternAnnotator

            source = kwargs.get("source")
            layer = kwargs.get("layer", "pattern")
            ignore_case = kwargs.get("ignore_case", True)
            word_boundaries = kwargs.get("word_boundaries", True)
            conflict_strategy = kwargs.get("conflict_strategy", "longest_priority")

            if source is None:
                raise ValueError("pattern annotator requires source")

            return PatternAnnotator(
                source=source,
                layer=layer,
                ignore_case=ignore_case,
                word_boundaries=word_boundaries,
                conflict_strategy=conflict_strategy,
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
                reference_datetime_metadata_key=kwargs.get(
                    "reference_datetime_metadata_key"
                ),
            )

        if name == "quantity":
            from umuannotator.annotators.quantity import QuantityAnnotator

            return QuantityAnnotator(
                language=language,
                locale=kwargs.get("locale"),
                timezone=kwargs.get("timezone", "Europe/Madrid"),
                layer=kwargs.get("layer", "cantidades"),
            )

        if name == "temporal":
            from umuannotator.annotators.temporal import TemporalAnnotator

            return TemporalAnnotator(
                language=language,
                locale=kwargs.get("locale"),
                timezone=kwargs.get(
                    "timezone",
                    "Europe/Madrid",
                ),
                layer=kwargs.get(
                    "layer",
                    "temporal",
                ),
                reference_datetime_metadata_key=kwargs.get(
                    "reference_datetime_metadata_key"
                ),
            )

        if name == "lexical-semantics":
            from umuannotator.annotators.lexical_semantics import (
                LexicalSemanticAnnotator,
            )

            source = kwargs.get("source")

            if source is None:
                raise ValueError(
                    "lexical-semantics annotator requires source"
                )

            source_path = Path(source)

            with source_path.open(
                encoding="utf-8",
            ) as file:
                resource = yaml.safe_load(file) or {}

            lexicon = resource.get("lexicon")
            semantic_classes = resource.get(
                "semantic_classes"
            )

            if not lexicon:
                raise ValueError(
                    "lexical-semantics resource requires lexicon"
                )

            if not semantic_classes:
                raise ValueError(
                    "lexical-semantics resource requires "
                    "semantic_classes"
                )

            resource_language = resource.get(
                "language",
                language,
            )

            return LexicalSemanticAnnotator(
                language=resource_language,
                lexicon=lexicon,
                semantic_classes=semantic_classes,
                layer=kwargs.get(
                    "layer",
                    "lexical_semantics",
                ),
                max_hypernym_depth=kwargs.get(
                    "max_hypernym_depth",
                    10,
                ),
            )

        raise ValueError(f"Unknown annotator: {name}")


def build_annotators(
    names: list,
    *,
    language: str = "es",
    ontology_path: str | None = None,
    config: dict | None = None,
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
                config=config,
                **params,
            )
        )

    return annotators