import math
import networkx as nx

from umuannotator.document import Corpus


class ExtendedTfidfScorer:
    def __init__(
        self,
        ontology_graph,
        decay: float = 0.5,
        max_distance: int = 5,
        layer: str = "ontology",
        decay_function: str = "exponential",
    ):
        self.ontology_graph = ontology_graph
        self.decay = decay
        self.max_distance = max_distance
        self.layer = layer
        self.decay_function = decay_function

    def score(self, corpus: Corpus) -> Corpus:
        for document in corpus.documents:
            scores: dict[str, float] = {}

            for annotation in document.annotations:
                if annotation.layer != self.layer:
                    continue

                if annotation.score is None:
                    continue

                distances = self._distances(annotation.label)

                for concept, distance in distances.items():
                    contribution = annotation.score * self._distance_weight(distance)
                    scores[concept] = scores.get(concept, 0.0) + contribution

            document.metadata["tfidf_extended"] = scores

        return corpus

    def _distance_weight(self, distance: float) -> float:
        if self.decay_function == "exponential":
            return self.decay ** distance

        if self.decay_function == "inverse":
            return 1 / (1 + distance)

        if self.decay_function == "none":
            return 1.0

        raise ValueError(f"Unknown decay function: {self.decay_function}")

    def _distances(self, concept: str) -> dict[str, float]:
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