from __future__ import annotations

from time import perf_counter

from tqdm import tqdm

from umuannotator.document import Corpus, Document


class AnnotationEnrichmentPipeline:
    def __init__(
        self,
        enrichers=None,
    ):
        self.enrichers = enrichers or []
        self.timings: dict[str, float] = {}

    def run_document(
        self,
        document: Document,
    ) -> Document:
        for enricher in self.enrichers:
            name = enricher.__class__.__name__

            start = perf_counter()
            document = enricher.enrich(document)
            elapsed = perf_counter() - start

            self.timings[name] = (
                self.timings.get(name, 0.0)
                + elapsed
            )

        return document

    def run_corpus(
        self,
        corpus: Corpus,
        show_progress: bool = True,
        desc: str = "Enriching annotations",
    ) -> Corpus:
        documents = corpus.documents

        if show_progress:
            documents = tqdm(
                documents,
                desc=desc,
            )

        corpus.documents = [
            self.run_document(document)
            for document in documents
        ]

        return corpus