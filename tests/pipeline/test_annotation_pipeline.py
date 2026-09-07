from umuannotator.document import Annotation, Corpus, Document
from umuannotator.pipeline import AnnotationPipeline

events = []

class P1:
    def process_document(self, document):
        events.append("pre")
        return document


class A1:
    def annotate(self, document):
        events.append("ann")
        return document

class DummyPreprocessor:
    def process_document(self, document):
        document.metadata["preprocessed"] = True
        return document


class SimpleAnnotator:
    def annotate(self, document):
        return document

class SecondPreprocessor:
    def process_document(self, document):
        document.metadata["second"] = True
        return document


class DummyAnnotator:
    def annotate(self, document):
        document.add_annotation(
            Annotation(
                start=0,
                end=4,
                text="test",
                label="TEST",
                layer="dummy",
            )
        )

        return document


class PreprocessAwareAnnotator:
    def annotate(self, document):
        assert document.metadata["preprocessed"] is True

        document.add_annotation(
            Annotation(
                start=0,
                end=4,
                text="test",
                label="TEST",
                layer="dummy",
            )
        )

        return document
    

class SecondPreprocessor:
    def preprocess(self, document):
        document.metadata["second"] = True
        return document


def test_pipeline_runs_preprocessors_before_annotators():
    pipeline = AnnotationPipeline(
        preprocessors=[DummyPreprocessor()],
        annotators=[PreprocessAwareAnnotator()],
    )

    corpus = Corpus(
        documents=[
            Document(text="test"),
        ]
    )

    result = pipeline.run_corpus(
        corpus,
        show_progress=False,
    )

    document = result.documents[0]

    assert document.metadata["preprocessed"] is True
    assert len(document.annotations) == 1

    

def test_pipeline_collects_annotator_timings():
    pipeline = AnnotationPipeline(
        annotators=[DummyAnnotator()],
    )

    corpus = Corpus(
        documents=[
            Document(text="test"),
        ]
    )

    pipeline.run_corpus(
        corpus,
        show_progress=False,
    )

    assert "DummyAnnotator" in pipeline.timings
    assert pipeline.timings["DummyAnnotator"] >= 0


def test_pipeline_accumulates_timings_over_documents():
    pipeline = AnnotationPipeline(
        annotators=[DummyAnnotator()],
    )

    corpus = Corpus(
        documents=[
            Document(text="one"),
            Document(text="two"),
            Document(text="three"),
        ]
    )

    pipeline.run_corpus(
        corpus,
        show_progress=False,
    )

    assert pipeline.timings["DummyAnnotator"] > 0


def test_pipeline_without_preprocessors():
    pipeline = AnnotationPipeline(
        annotators=[SimpleAnnotator()],
    )

    corpus = Corpus(
        documents=[
            Document(text="hello"),
        ]
    )

    result = pipeline.run_corpus(
        corpus,
        show_progress=False,
    )

    assert result.documents[0].text == "hello"


def test_pipeline_execution_order():
    events.clear()

    pipeline = AnnotationPipeline(
        preprocessors=[P1()],
        annotators=[A1()],
    )

    corpus = Corpus(
        documents=[
            Document(text="test"),
        ]
    )

    pipeline.run_corpus(
        corpus,
        show_progress=False,
    )

    assert events == ["pre", "ann"]