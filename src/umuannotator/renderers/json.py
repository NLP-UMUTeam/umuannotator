from umuannotator.document import Corpus

def annotation_to_dict(annotation):
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


def document_to_dict(document):
    return {
        "text": document.text,
        "metadata": document.metadata,
        "annotations": [
            annotation_to_dict(annotation)
            for annotation in document.annotations
        ],
    }


def corpus_to_dict(corpus_or_documents):
    if isinstance(corpus_or_documents, Corpus):
        documents = corpus_or_documents.documents
    else:
        documents = corpus_or_documents

    return {
        "documents": [
            document_to_dict(doc)
            for doc in documents
        ]
    }