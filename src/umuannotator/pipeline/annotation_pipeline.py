from umuannotator.document.model import Document


class AnnotationPipeline:
    def __init__(self, annotators: list): 
        self.annotators = annotators

    def run_text(self, text: str) -> Document:
        document = Document(text=text)

        for annotator in self.annotators:
            document = annotator.annotate(document)

        return document