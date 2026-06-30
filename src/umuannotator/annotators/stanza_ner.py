from __future__ import annotations

from umuannotator.document.model import Annotation, Document
from umuannotator.utils.silent import run_silent


class StanzaNERAnnotator:
    layer = "ner"

    def __init__(
        self,
        language: str = "es",
        layer: str = "ner",
    ):
        self.language = language
        self.layer = layer

        def build_pipeline():
            import stanza

            return stanza.Pipeline(
                lang=language,
                processors="tokenize,ner",
                verbose=False,
                use_gpu=False,
                download_method=None
            )

        self.pipeline = run_silent(build_pipeline)

    def annotate(self, document: Document) -> Document:
        stanza_doc = run_silent(
            lambda: self.pipeline(document.text),
        )

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