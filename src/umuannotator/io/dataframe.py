import json
from typing import Any

from umuannotator.document import Annotation, Corpus, Document


def dataframe_to_corpus(
    df,
    text_column: str,
    id_column: str | None = None,
) -> Corpus:
    corpus = Corpus()

    for index, row in df.iterrows():
        doc_id = row[id_column] if id_column else index

        document = Document(
            text=str(row[text_column]),
        )

        document.metadata["doc_id"] = doc_id

        corpus.append(document)

    return corpus


def corpus_to_documents_dataframe(corpus: Corpus):
    import pandas as pd

    rows: list[dict[str, Any]] = []

    for document_index, document in enumerate(corpus.documents):
        doc_id = document.metadata.get("doc_id", document_index)

        rows.append({
            "doc_id": doc_id,
            "text": document.text,
            "annotations": json.dumps([
                annotation_to_dict(annotation)
                for annotation in document.annotations
            ], ensure_ascii=False),
        })

    return pd.DataFrame(rows)


def corpus_to_annotations_dataframe(corpus: Corpus):
    import pandas as pd

    rows: list[dict[str, Any]] = []

    for document_index, document in enumerate(corpus.documents):
        doc_id = document.metadata.get("doc_id", document_index)

        for annotation in document.annotations:
            rows.append({
                "doc_id": doc_id,
                "start": annotation.start,
                "end": annotation.end,
                "text": annotation.text,
                "label": annotation.label,
                "layer": annotation.layer,
                "source": annotation.source,
                "type": annotation.type,
                "subtype": annotation.subtype,
                "score": annotation.score,
                "metadata": json.dumps(
                    annotation.metadata,
                    ensure_ascii=False, 
                ),
            })

    return pd.DataFrame(rows)


def annotation_to_dict(annotation: Annotation) -> dict[str, Any]:
    return {
        "start": annotation.start,
        "end": annotation.end,
        "text": annotation.text,
        "label": annotation.label,
        "layer": annotation.layer,
        "source": annotation.source,
        "type": annotation.type,
        "subtype": annotation.subtype,
        "score": annotation.score,
        "metadata": annotation.metadata,
    }