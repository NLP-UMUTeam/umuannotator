import math
from collections import Counter

from umuannotator.document import Corpus, Document


class TfidfScorer:
    def __init__(self, layer: str = "ontology"):
        self.layer = layer

    def score(self, corpus_or_documents):
        if isinstance(corpus_or_documents, Corpus):
            corpus_or_documents.documents = self._score_documents(
                corpus_or_documents.documents
            )
            return corpus_or_documents

        return self._score_documents(corpus_or_documents)

    def _score_documents(self, documents: list[Document]) -> list[Document]:
        if not documents:
            return documents

        document_frequency = self._document_frequency(documents)
        total_documents = len(documents)

        for document in documents:
            term_frequency = self._term_frequency(document)

            for annotation in document.annotations:
                if annotation.layer != self.layer:
                    continue

                label = annotation.label
                tf = term_frequency[label]
                df = document_frequency[label]

                idf = (
                    math.log(total_documents / df)
                    if df > 1
                    else 1.0
                )

                tfidf = tf * idf

                annotation.score = tfidf
                annotation.metadata["tf"] = tf
                annotation.metadata["df"] = df
                annotation.metadata["idf"] = idf
                annotation.metadata["tfidf"] = tfidf

        return documents

    def _term_frequency(self, document: Document) -> Counter:
        return Counter(
            annotation.label
            for annotation in document.annotations
            if annotation.layer == self.layer
        )

    def _document_frequency(self, documents: list[Document]) -> Counter:
        frequency = Counter()

        for document in documents:
            labels_in_document = {
                annotation.label
                for annotation in document.annotations
                if annotation.layer == self.layer
            }

            for label in labels_in_document:
                frequency[label] += 1

        return frequency