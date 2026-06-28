from __future__ import annotations

from time import perf_counter
from tqdm import tqdm


from umuannotator.document import Corpus, Document

class AnnotationPipeline:
    def __init__(
        self,
        annotators,
        preprocessors=None,
    ):
        self.annotators = annotators
        self.preprocessors = preprocessors or []
        self.timings: dict[str, float] = {}

    def run_text(self, text: str) -> Document:
        document = Document(text=text)
        return self.run_document(document)

    def run_texts(self, texts: list[str]) -> list[Document]:
        return [
            self.run_text(text)
            for text in texts
        ]


    def run_document(self, document: Document) -> Document:
        for preprocessor in self.preprocessors:
            name = preprocessor.__class__.__name__

            start = perf_counter()
            document = preprocessor.process_document(document)
            elapsed = perf_counter() - start

            self.timings[name] = self.timings.get(name, 0.0) + elapsed

        for annotator in self.annotators:
            name = annotator.__class__.__name__

            start = perf_counter()
            document = annotator.annotate(document)
            elapsed = perf_counter() - start

            self.timings[name] = self.timings.get(name, 0.0) + elapsed

        return document


    def run_corpus(
        self,
        corpus: Corpus,
        show_progress: bool = True,
        desc: str = "Annotating documents",
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