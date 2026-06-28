import re

from umuannotator.document.model import Annotation, Document


def split_camel_case(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", " ", value)


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
        matching_config: dict | None = None,
    ):
        self.concepts = concepts
        self.source = source
        self.matching_config = matching_config or {}

        fields = self.matching_config.get("fields", {})

        self.match_labels = fields.get("labels", True)
        self.match_aliases = fields.get("aliases", True)
        self.match_patterns = fields.get("patterns", True)
        self.match_name = fields.get("name", False)
        self.match_name_camel_case = fields.get("name_camel_case", True)

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
            if self.match_labels or self.match_aliases or self.match_name:
                self._annotate_terms(
                    document=document,
                    text=text,
                    concept_uri=concept_uri,
                    concept=concept,
                )

            if self.match_patterns:
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
        terms: list[tuple[str, str]] = []

        if self.match_labels:
            terms.extend((label, "label") for label in concept.labels)

        if self.match_aliases:
            terms.extend((alias, "alias") for alias in concept.aliases)

        if self.match_name:
            terms.append((concept.name, "name"))

            if self.match_name_camel_case:
                split_name = split_camel_case(concept.name)

                if split_name != concept.name:
                    terms.append((split_name, "name_camel_case"))

        for term, match_source in terms:
            if not term:
                continue

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
                    match_source=match_source,
                    matched_value=term,
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
                    matched_value=pattern,
                )

    def _add_annotation(
        self,
        document: Document,
        match,
        concept_uri: str,
        concept,
        match_source: str,
        matched_value: str,
    ) -> None:
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
                    "matched_value": matched_value,
                },
            )
        )