from __future__ import annotations

from umuannotator.document import Corpus, Document
from umuannotator.pipeline import RelationEnrichmentPipeline


class DummyRelationEnricher:
    def enrich(
        self,
        document: Document,
    ) -> Document:
        document.metadata["enriched"] = True
        return document


def test_relation_enrichment_pipeline_with_no_enrichers():
    document = Document(
        text="Texto de prueba.",
    )
    corpus = Corpus(
        documents=[document],
    )

    pipeline = RelationEnrichmentPipeline(
        enrichers=[],
    )

    result = pipeline.run_corpus(
        corpus,
        show_progress=False,
    )

    assert result is corpus
    assert len(result.documents) == 1
    assert result.documents[0].text == "Texto de prueba."
    assert "enriched" not in result.documents[0].metadata


def test_relation_enrichment_pipeline_runs_enricher():
    document = Document(
        text="Texto de prueba.",
    )
    corpus = Corpus(
        documents=[document],
    )

    pipeline = RelationEnrichmentPipeline(
        enrichers=[
            DummyRelationEnricher(),
        ],
    )

    result = pipeline.run_corpus(
        corpus,
        show_progress=False,
    )

    assert result.documents[0].metadata["enriched"] is True


def test_relation_enrichment_pipeline_records_timings():
    document = Document(
        text="Texto de prueba.",
    )
    corpus = Corpus(
        documents=[document],
    )

    pipeline = RelationEnrichmentPipeline(
        enrichers=[
            DummyRelationEnricher(),
        ],
    )

    pipeline.run_corpus(
        corpus,
        show_progress=False,
    )

    assert "DummyRelationEnricher" in pipeline.timings
    assert pipeline.timings["DummyRelationEnricher"] >= 0.0


def test_relation_enrichment_pipeline_runs_multiple_enrichers():
    class FirstEnricher:
        def enrich(
            self,
            document: Document,
        ) -> Document:
            document.metadata.setdefault(
                "steps",
                [],
            ).append("first")
            return document

    class SecondEnricher:
        def enrich(
            self,
            document: Document,
        ) -> Document:
            document.metadata.setdefault(
                "steps",
                [],
            ).append("second")
            return document

    document = Document(
        text="Texto de prueba.",
    )
    corpus = Corpus(
        documents=[document],
    )

    pipeline = RelationEnrichmentPipeline(
        enrichers=[
            FirstEnricher(),
            SecondEnricher(),
        ],
    )

    result = pipeline.run_corpus(
        corpus,
        show_progress=False,
    )

    assert result.documents[0].metadata["steps"] == [
        "first",
        "second",
    ]