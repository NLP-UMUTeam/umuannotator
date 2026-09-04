from __future__ import annotations

from time import perf_counter

from tqdm import tqdm

from umuannotator.document import Corpus, Document


class RelationExtractionPipeline:
    def __init__(
        self,
        extractors=None,
    ):
        self.extractors = extractors or []
        self.timings: dict[str, float] = {}

    def run_document(
        self,
        document: Document,
    ) -> Document:
        for extractor in self.extractors:
            name = extractor.__class__.__name__

            start = perf_counter()
            document = extractor.extract(document)
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
        desc: str = "Extracting relations",
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