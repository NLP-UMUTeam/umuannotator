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


def relation_predicate_to_dict(predicate):
    return {
        "start": predicate.start,
        "end": predicate.end,
        "text": predicate.text,
        "lemma": predicate.lemma,
        "metadata": predicate.metadata,
    }


def relation_argument_to_dict(argument):
    return {
        "role": argument.role,
        "start": argument.start,
        "end": argument.end,
        "text": argument.text,
        "annotation_id": argument.annotation_id,
        "metadata": argument.metadata,
    }


def relation_to_dict(relation):
    return {
        "id": relation.id,
        "type": relation.type,
        "predicate": relation_predicate_to_dict(
            relation.predicate
        ),
        "arguments": [
            relation_argument_to_dict(argument)
            for argument in relation.arguments
        ],
        "source": relation.source,
        "score": relation.score,
        "metadata": relation.metadata,
    }


def document_to_dict(document):
    return {
        "text": document.text,
        "metadata": document.metadata,
        "annotations": [
            annotation_to_dict(annotation)
            for annotation in document.annotations
        ],
        "relations": [
            relation_to_dict(relation)
            for relation in document.relations
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