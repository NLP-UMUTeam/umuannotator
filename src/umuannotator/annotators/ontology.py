import re

from umuannotator.document.model import Annotation, Document


class OntologyAnnotator:
    """
    Ontology-based semantic annotator.

    Concepts are matched using ontology labels, aliases and configured
    regex patterns extracted from the RDF/OWL index.

    Design notes
    ------------
    Concept URIs are the stable internal identifiers.

    Generated annotations use:

        label
            Human-readable concept name.

        metadata["concept_id"]
            Stable ontology URI used by graph-based semantic scoring.
    """

    layer = "ontology"

    def __init__(
        self,
        concepts: dict,
        source: str | None = None,
    ):
        self.concepts = concepts
        self.source = source

    def annotate(
        self,
        document: Document,
    ) -> Document:
        """
        Annotate ontology concepts found in document text.

        Matching currently supports two sources:

        - literal terms from rdfs:label and rdfs:seeAlso
        - regex patterns from the configured ontology regex property

        Literal terms are escaped and wrapped with word boundaries.
        Ontology regex patterns are used directly.
        """
        text = document.text

        for concept_uri, concept in self.concepts.items():
            self._annotate_terms(
                document=document,
                text=text,
                concept_uri=concept_uri,
                concept=concept,
            )

            self._annotate_patterns(
                document=document,
                text=text,
                concept_uri=concept_uri,
                concept=concept,
            )

        return document

    def _annotate_terms(
        self,
        document: Document,
        text: str,
        concept_uri: str,
        concept,
    ) -> None:
        """
        Annotate literal labels and aliases.

        These values are treated as plain text, not as regular
        expressions.
        """
        terms = []

        terms.extend(concept.labels)
        terms.extend(concept.aliases)

        for term in terms:
            pattern = rf"\b{re.escape(term)}\b"

            for match in re.finditer(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                self._add_annotation(
                    document=document,
                    match=match,
                    concept_uri=concept_uri,
                    concept=concept,
                    match_source="term",
                )

    def _annotate_patterns(
        self,
        document: Document,
        text: str,
        concept_uri: str,
        concept,
    ) -> None:
        """
        Annotate configured ontology regex patterns.

        Regex patterns are read from concept.patterns and used directly.
        This allows ontology authors to define alternatives such as:

            pizza\\s+hawaiana|hawaiana
        """
        for pattern in concept.patterns:
            for match in re.finditer(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                self._add_annotation(
                    document=document,
                    match=match,
                    concept_uri=concept_uri,
                    concept=concept,
                    match_source="regex",
                )

    def _add_annotation(
        self,
        document: Document,
        match,
        concept_uri: str,
        concept,
        match_source: str,
    ) -> None:
        """
        Add a normalized ontology annotation.

        The annotation keeps a readable label while preserving the URI
        required by graph-based metrics.
        """
        document.add_annotation(
            Annotation(
                start=match.start(),
                end=match.end(),
                text=match.group(),
                label=concept.name,
                layer=self.layer,
                source=self.source,
                type="ontology",
                metadata={
                    "concept_id": concept_uri,
                    "concept_uri": concept_uri,
                    "concept_name": concept.name,
                    "entity_type": concept.entity_type,
                    "match_source": match_source,
                },
            )
        )