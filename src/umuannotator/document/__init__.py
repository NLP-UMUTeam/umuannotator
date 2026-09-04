from umuannotator.document.model import (
    Annotation,
    Document,
    Relation,
    RelationArgument,
    RelationPredicate,
)
from .corpus import Corpus
from .resolver import AnnotationResolver

__all__ = [
    "Annotation",
    "Document",
    "Relation",
    "RelationArgument",
    "RelationPredicate",
    "Corpus",
    "AnnotationResolver",
]