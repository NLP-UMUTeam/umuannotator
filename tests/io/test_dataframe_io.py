import pandas as pd

from umuannotator.io.dataframe import (
    dataframe_to_corpus,
    corpus_to_annotations_dataframe,
)
from umuannotator.annotators.registry import build_annotators
from umuannotator.pipeline import AnnotationPipeline


def test_dataframe_to_corpus_and_annotations_dataframe():
    df = pd.DataFrame([
        {"id": "doc-1", "text": "Me gusta la pizza hawaiana."},
        {"id": "doc-2", "text": "Me gusta la pizza margarita."},
    ])

    corpus = dataframe_to_corpus(
        df,
        text_column="text",
        id_column="id",
    )

    annotators = build_annotators(
        ["ontology"],
        ontology_path="resources/pizza.owl",
        language="es",
    )

    pipeline = AnnotationPipeline(annotators)
    corpus = pipeline.run_corpus(corpus)

    annotations_df = corpus_to_annotations_dataframe(corpus)

    assert len(corpus) == 2
    assert "HawaiianPizza" in set(annotations_df["label"])
    assert "doc-1" in set(annotations_df["doc_id"])