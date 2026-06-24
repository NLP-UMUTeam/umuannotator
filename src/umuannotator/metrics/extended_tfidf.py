import networkx as nx

from umuannotator.document import Corpus


class ExtendedTfidfScorer:
    """
    Semantic TF-IDF expansion over an ontology graph.

    The scorer starts from ontology annotations already weighted by
    TF-IDF and propagates their scores through the ontology graph.

    Propagation uses shortest semantic distances computed with
    Dijkstra's algorithm.

    Design notes
    ------------
    Ontology graph nodes are stable concept URIs.

    Human-readable annotation labels are not used for graph traversal.
    Instead, annotations are expected to store the ontology URI in:

        annotation.metadata["concept_id"]

    If an old annotation does not contain ``concept_id``, the scorer
    falls back to ``annotation.label`` for backward compatibility.

    Results are stored in:

        document.metadata["tfidf_extended"]
    """

    def __init__(
        self,
        ontology_graph,
        decay: float = 0.5,
        max_distance: int = 5,
        layer: str = "ontology",
        decay_function: str = "exponential",
        aggregation: str = "sum",
    ):
        """
        Parameters
        ----------
        ontology_graph
            Directed ontology graph.

        decay
            Base decay parameter used by the exponential decay
            function.

        max_distance
            Maximum semantic distance explored during propagation.

        layer
            Annotation layer to process.

        decay_function
            One of:

            - exponential
            - inverse
            - none

        aggregation
            Strategy used when multiple propagated paths contribute
            to the same concept.

            Supported values:

            - sum
            - max
        """
        self.ontology_graph = ontology_graph
        self.decay = decay
        self.max_distance = max_distance
        self.layer = layer
        self.decay_function = decay_function
        self.aggregation = aggregation

    def score(self, corpus: Corpus) -> Corpus:
        """
        Compute ontology-expanded TF-IDF scores.

        For every ontology annotation:

        1. Read the stable concept URI from annotation metadata.
        2. Compute reachable concepts in the ontology graph.
        3. Obtain shortest semantic distances.
        4. Apply decay.
        5. Aggregate contributions.

        The resulting concept scores are stored in:

            document.metadata["tfidf_extended"]

        The keys of this dictionary are concept URIs.
        """
        for document in corpus.documents:
            scores: dict[str, float] = {}

            for annotation in document.annotations:
                if annotation.layer != self.layer:
                    continue

                if annotation.score is None:
                    continue

                concept_id = self._annotation_concept_id(
                    annotation,
                )

                distances = self._distances(concept_id)

                for concept, distance in distances.items():
                    contribution = (
                        annotation.score
                        * self._distance_weight(distance)
                    )

                    self._aggregate(
                        scores,
                        concept,
                        contribution,
                    )

            document.metadata["tfidf_extended"] = scores

        return corpus

    def _annotation_concept_id(
        self,
        annotation,
    ) -> str:
        """
        Return the stable ontology identifier for an annotation.

        New ontology annotations should provide:

            annotation.metadata["concept_id"]

        For backward compatibility, annotations without concept metadata
        fall back to:

            annotation.label
        """
        return annotation.metadata.get(
            "concept_id",
            annotation.label,
        )

    def _aggregate(
        self,
        scores: dict[str, float],
        concept: str,
        contribution: float,
    ) -> None:
        """
        Aggregate a propagated contribution.

        sum
            Adds all contributions.

        max
            Keeps only the strongest contribution reaching a concept.
        """
        if self.aggregation == "sum":
            scores[concept] = (
                scores.get(concept, 0.0)
                + contribution
            )
            return

        if self.aggregation == "max":
            scores[concept] = max(
                scores.get(concept, 0.0),
                contribution,
            )
            return

        raise ValueError(
            f"Unknown aggregation: {self.aggregation}"
        )

    def _distance_weight(
        self,
        distance: float,
    ) -> float:
        """
        Convert semantic distance into a propagation weight.

        exponential
            decay ** distance

        inverse
            1 / (1 + distance)

        none
            Constant weight of 1.0
        """
        if self.decay_function == "exponential":
            return self.decay ** distance

        if self.decay_function == "inverse":
            return 1 / (1 + distance)

        if self.decay_function == "none":
            return 1.0

        raise ValueError(
            f"Unknown decay function: {self.decay_function}"
        )

    def _distances(
        self,
        concept: str,
    ) -> dict[str, float]:
        """
        Compute shortest semantic distances from a concept URI.

        Distances are obtained using Dijkstra's algorithm over the
        directed ontology graph.

        The graph stores semantic distances in the edge attribute
        ``weight`` because that is the NetworkX convention.

        Returns
        -------
        dict[str, float]

            Mapping:

                concept_uri -> semantic distance
        """
        if concept not in self.ontology_graph:
            return {}

        return dict(
            nx.single_source_dijkstra_path_length(
                self.ontology_graph,
                concept,
                cutoff=self.max_distance,
                weight="weight",
            )
        )