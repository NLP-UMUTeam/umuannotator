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

        - literal terms from rdfs:label, rdfs:seeAlso and concept names
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
        Annotate literal labels, aliases and concept names.

        These values are treated as plain text, not as regular
        expressions. They are escaped and wrapped with word boundaries
        to avoid matches inside longer words.

        Example:
            IA matches "La IA avanza"
            IA does not match "Francia" or "Alemania"
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

            pattern = self._literal_to_regex(term)

            self._annotate_regex_match(
                document=document,
                text=text,
                concept_uri=concept_uri,
                concept=concept,
                pattern=pattern,
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

        Regex patterns are read from concept.patterns.

        They are not escaped, so ontology authors can still define regex
        alternatives such as:

            pizza\\s+hawaiana|hawaiana
            pizza(s)?

        However, they are wrapped with word boundaries to avoid short regex
        patterns such as "IA" matching inside longer words such as
        "Francia" or "Alemania".
        """
        for pattern in concept.patterns:
            bounded_pattern = self._regex_with_boundaries(pattern)

            self._annotate_regex_match(
                document=document,
                text=text,
                concept_uri=concept_uri,
                concept=concept,
                pattern=bounded_pattern,
                match_source="regex",
                matched_value=pattern,
            )

    def _literal_to_regex(self, value: str) -> str:
        """
        Convert a literal ontology value into a safe regex.

        Used for labels, aliases, concept names and camel-case names.

        This prevents short literals such as "IA" from matching inside
        longer words like "Francia" or "Alemania".
        """
        return rf"(?<!\w){re.escape(value)}(?!\w)"

    def _annotate_regex_match(
        self,
        document: Document,
        text: str,
        concept_uri: str,
        concept,
        pattern: str,
        match_source: str,
        matched_value: str,
    ) -> None:
        """
        Apply a regex pattern to text and add one annotation per match.

        For literal ontology values, pattern should come from
        _literal_to_regex(...).

        For ontology regex patterns, pattern should be used directly.
        """
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
                matched_value=matched_value,
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

    def _regex_with_boundaries(self, pattern: str) -> str:
        """
        Wrap a regex pattern with word boundaries without escaping it.

        This preserves regex behavior while preventing matches inside words.

        Example:
            pizza(s)?  -> (?<!\\w)(?:pizza(s)?)(?!\\w)

        So it still matches:
            pizza
            pizzas

        But it avoids:
            IA inside Francia
            IA inside Alemania
        """
        return rf"(?<!\w)(?:{pattern})(?!\w)"