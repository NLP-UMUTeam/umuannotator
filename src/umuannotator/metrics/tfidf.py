from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping

from umuannotator.document import Corpus, Document


class TfidfScorer: 
    def __init__(
        self,
        layer: str = "ontology",
    ):
        self.layer = layer

        self.total_documents = 0
        self.document_frequency: Counter = Counter()
        self._fitted = False

    def score(
        self,
        corpus_or_documents,
    ):
        """
        Fit TF-IDF statistics on the supplied corpus and score all
        documents.

        This preserves the original one-step API.
        """
        if isinstance(
            corpus_or_documents,
            Corpus,
        ):
            documents = (
                corpus_or_documents.documents
            )

            self.fit(documents)

            for document in documents:
                self.score_document(
                    document
                )

            return corpus_or_documents

        documents = corpus_or_documents

        self.fit(documents)

        for document in documents:
            self.score_document(
                document
            )

        return documents

    def fit(
        self,
        documents: list[Document],
    ) -> TfidfScorer:
        """
        Compute corpus-level TF-IDF statistics.
        """
        self.total_documents = len(
            documents
        )

        self.document_frequency = (
            self._document_frequency(
                documents
            )
        )

        self._fitted = True

        return self

    def fit_statistics(
        self,
        *,
        total_documents: int,
        document_frequency: Mapping[
            str,
            int,
        ],
    ) -> TfidfScorer:
        """
        Set corpus-level TF-IDF statistics computed externally.

        This is intended for streaming workflows where corpus
        statistics are collected in a first pass and documents are
        scored individually in a second pass.
        """
        self.total_documents = (
            total_documents
        )

        self.document_frequency = Counter(
            document_frequency
        )

        self._fitted = True

        return self

    def score_document(
        self,
        document: Document,
    ) -> Document:
        """
        Apply previously fitted TF-IDF statistics to one document.
        """
        if not self._fitted:
            raise RuntimeError(
                "TfidfScorer must be fitted "
                "before scoring documents."
            )

        term_frequency = (
            self._term_frequency(
                document
            )
        )

        for annotation in document.annotations:
            if annotation.layer != self.layer:
                continue

            label = annotation.label

            tf = term_frequency[label]
            df = self.document_frequency[
                label
            ]

            idf = (
                math.log(
                    self.total_documents / df
                )
                if df > 1
                else 1.0
            )

            tfidf = tf * idf

            annotation.score = tfidf

            annotation.metadata["tf"] = tf
            annotation.metadata["df"] = df
            annotation.metadata["idf"] = idf
            annotation.metadata[
                "tfidf"
            ] = tfidf

        return document

    def _term_frequency(
        self,
        document: Document,
    ) -> Counter:
        return Counter(
            annotation.label
            for annotation
            in document.annotations
            if annotation.layer
            == self.layer
        )

    def _document_frequency(
        self,
        documents: list[Document],
    ) -> Counter:
        frequency = Counter()

        for document in documents:
            labels_in_document = {
                annotation.label
                for annotation
                in document.annotations
                if annotation.layer
                == self.layer
            }

            for label in labels_in_document:
                frequency[label] += 1

        return frequency