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

        if name == "temporal":
            from umuannotator.annotators.temporal import TemporalAnnotator

            return TemporalAnnotator(language=language)

        raise ValueError(f"Unknown annotator: {name}")


def build_annotators( 
    names: list[str],
    *,
    language: str = "es",
    ontology_path: str | None = None,
):
    factory = AnnotatorFactory()

    return [
        factory.create(
            name,
            language=language,
            ontology_path=ontology_path,
        )
        for name in names
    ]