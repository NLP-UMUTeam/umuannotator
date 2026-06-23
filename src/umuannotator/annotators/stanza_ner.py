from umuannotator.document.model import Annotation, Document


class StanzaNERAnnotator: 
    layer = "ner"

    def __init__(self, language: str = "es"):
        import stanza

        self.language = language
        self.pipeline = stanza.Pipeline(
            lang=language,
            processors="tokenize,ner",
            verbose=False,
            use_gpu=False,
        )

    def annotate(self, document: Document) -> Document:
        stanza_doc = self.pipeline(document.text)

        for entity in stanza_doc.ents:
            document.add_annotation(
                Annotation(
                    start=entity.start_char,
                    end=entity.end_char,
                    text=entity.text,
                    label=entity.type,
                    layer=self.layer,
                    source="stanza",
                    type="ner",
                    subtype=entity.type,
                    metadata={
                        "language": self.language,
                    },
                )
            )

        return document