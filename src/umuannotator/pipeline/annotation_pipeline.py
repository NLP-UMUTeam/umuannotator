from umuannotator.document import Corpus, Document


class AnnotationPipeline:
    def __init__(self, annotators: list):
        self.annotators = annotators

    def run_text(self, text: str) -> Document:
        document = Document(text=text)
        return self.run_document(document)

    def run_texts(self, texts: list[str]) -> list[Document]:
        return [
            self.run_text(text)
            for text in texts
        ]

    def run_document(self, document: Document) -> Document:
        for annotator in self.annotators:
            document = annotator.annotate(document)

        return document

    def run_corpus(self, corpus: Corpus) -> Corpus:
        corpus.documents = [
            self.run_document(document)
            for document in corpus.documents
        ]

        return corpus