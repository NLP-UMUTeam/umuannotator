import re

from umuannotator.document.model import Annotation, Document


class OntologyAnnotator:
    layer = "ontology"

    def __init__(self, concepts: dict, source: str | None = None):
        self.concepts = concepts
        self.source = source

    def annotate(self, document: Document) -> Document:
        text = document.text

        for concept_name, concept in self.concepts.items():
            terms = []

            terms.extend(concept.labels)
            terms.extend(concept.aliases)

            for term in terms:
                pattern = rf"\b{re.escape(term)}\b"

                for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                    document.add_annotation(
                        Annotation(
                            start=match.start(),
                            end=match.end(),
                            text=match.group(),
                            label=concept_name,
                            layer=self.layer,
                            source=self.source,
                            type="ontology",
                        )
                    )

        return document