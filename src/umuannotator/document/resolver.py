from umuannotator.document.model import Annotation, Document


class AnnotationResolver:
    def __init__(self, layer: str | None = None):
        self.layer = layer

    def resolve_document(self, document: Document) -> Document:
        candidates = [
            annotation
            for annotation in document.annotations
            if self.layer is None or annotation.layer == self.layer
        ]

        others = [
            annotation
            for annotation in document.annotations
            if self.layer is not None and annotation.layer != self.layer
        ]

        resolved = self._longest_match_wins(candidates)
        document.annotations = sorted(
            others + resolved,
            key=lambda annotation: (
                annotation.start,
                annotation.end,
                annotation.layer,
                annotation.label,
            ),
        )

        return document

    def resolve_corpus(self, corpus):
        corpus.documents = [
            self.resolve_document(document)
            for document in corpus.documents
        ]
        return corpus

    def _longest_match_wins(
        self,
        annotations: list[Annotation],
    ) -> list[Annotation]:
        annotations = sorted(
            annotations,
            key=lambda annotation: (
                -(annotation.end - annotation.start),
                annotation.start,
                annotation.label,
            ),
        )

        selected: list[Annotation] = []

        for annotation in annotations:
            if not self._overlaps_any(annotation, selected):
                selected.append(annotation)

        return selected

    def _overlaps_any(
        self,
        annotation: Annotation,
        selected: list[Annotation],
    ) -> bool:
        return any(
            annotation.start < other.end and other.start < annotation.end
            for other in selected
        )