from umuannotator.document import Document
from umuannotator.relation_extractors.copular_predication import (
    CopularPredicationRelationExtractor,
)

def test_extract_adjectival_copular_predication():
    document = Document(
        text="La situación es crítica.",
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "La",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                                "start": 0,
                                "end": 2,
                            },
                            {
                                "id": 2,
                                "text": "situación",
                                "lemma": "situación",
                                "upos": "NOUN",
                                "head": 4,
                                "deprel": "nsubj",
                                "start": 3,
                                "end": 12,
                            },
                            {
                                "id": 3,
                                "text": "es",
                                "lemma": "ser",
                                "upos": "AUX",
                                "feats": (
                                    "Mood=Ind|Number=Sing|Person=3|"
                                    "Tense=Pres|VerbForm=Fin"
                                ),
                                "head": 4,
                                "deprel": "cop",
                                "start": 13,
                                "end": 15,
                            },
                            {
                                "id": 4,
                                "text": "crítica",
                                "lemma": "crítico",
                                "upos": "ADJ",
                                "head": 0,
                                "deprel": "root",
                                "start": 16,
                                "end": 23,
                            },
                            {
                                "id": 5,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 4,
                                "deprel": "punct",
                                "start": 23,
                                "end": 24,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = CopularPredicationRelationExtractor()

    extractor.extract(document)

    assert len(document.relations) == 1

    relation = document.relations[0]

    assert relation.type == "predicate_argument"
    assert relation.predicate.text == "crítica"
    assert relation.predicate.lemma == "crítico"

    assert len(relation.arguments) == 1
    assert relation.arguments[0].role == "subject"
    assert relation.arguments[0].text == "La situación"

    assert relation.metadata["rule"] == "copular_predication"
    assert relation.metadata["copula"] == "ser"

def test_extract_nominal_copular_predication():
    document = Document(
        text="Madrid es la capital.",
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "Madrid",
                                "lemma": "Madrid",
                                "upos": "PROPN",
                                "head": 4,
                                "deprel": "nsubj",
                                "start": 0,
                                "end": 6,
                            },
                            {
                                "id": 2,
                                "text": "es",
                                "lemma": "ser",
                                "upos": "AUX",
                                "head": 4,
                                "deprel": "cop",
                                "start": 7,
                                "end": 9,
                            },
                            {
                                "id": 3,
                                "text": "la",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 4,
                                "deprel": "det",
                                "start": 10,
                                "end": 12,
                            },
                            {
                                "id": 4,
                                "text": "capital",
                                "lemma": "capital",
                                "upos": "NOUN",
                                "head": 0,
                                "deprel": "root",
                                "start": 13,
                                "end": 20,
                            },
                            {
                                "id": 5,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 4,
                                "deprel": "punct",
                                "start": 20,
                                "end": 21,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = CopularPredicationRelationExtractor()

    extractor.extract(document)

    assert len(document.relations) == 1

    relation = document.relations[0]

    assert relation.predicate.lemma == "capital"
    assert relation.arguments[0].text == "Madrid"
    assert relation.metadata["copula"] == "ser"

def test_extract_copular_predication_with_estar():
    document = Document(
        text="El paciente está estable.",
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "El",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                                "start": 0,
                                "end": 2,
                            },
                            {
                                "id": 2,
                                "text": "paciente",
                                "lemma": "paciente",
                                "upos": "NOUN",
                                "head": 4,
                                "deprel": "nsubj",
                                "start": 3,
                                "end": 11,
                            },
                            {
                                "id": 3,
                                "text": "está",
                                "lemma": "estar",
                                "upos": "AUX",
                                "head": 4,
                                "deprel": "cop",
                                "start": 12,
                                "end": 16,
                            },
                            {
                                "id": 4,
                                "text": "estable",
                                "lemma": "estable",
                                "upos": "ADJ",
                                "head": 0,
                                "deprel": "root",
                                "start": 17,
                                "end": 24,
                            },
                            {
                                "id": 5,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 4,
                                "deprel": "punct",
                                "start": 24,
                                "end": 25,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = CopularPredicationRelationExtractor()

    extractor.extract(document)

    assert len(document.relations) == 1
    assert document.relations[0].metadata["copula"] == "estar"

def test_extract_negative_copular_predication():
    document = Document(
        text="La red no está operativa.",
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "La",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                                "start": 0,
                                "end": 2,
                            },
                            {
                                "id": 2,
                                "text": "red",
                                "lemma": "red",
                                "upos": "NOUN",
                                "head": 5,
                                "deprel": "nsubj",
                                "start": 3,
                                "end": 6,
                            },
                            {
                                "id": 3,
                                "text": "no",
                                "lemma": "no",
                                "upos": "ADV",
                                "feats": "Polarity=Neg",
                                "head": 5,
                                "deprel": "advmod",
                                "start": 7,
                                "end": 9,
                            },
                            {
                                "id": 4,
                                "text": "está",
                                "lemma": "estar",
                                "upos": "AUX",
                                "head": 5,
                                "deprel": "cop",
                                "start": 10,
                                "end": 14,
                            },
                            {
                                "id": 5,
                                "text": "operativa",
                                "lemma": "operativo",
                                "upos": "ADJ",
                                "head": 0,
                                "deprel": "root",
                                "start": 15,
                                "end": 24,
                            },
                            {
                                "id": 6,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 5,
                                "deprel": "punct",
                                "start": 24,
                                "end": 25,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = CopularPredicationRelationExtractor()

    extractor.extract(document)

    assert len(document.relations) == 1
    assert document.relations[0].metadata["polarity"] == "negative"

def test_adjective_without_copula_does_not_create_relation():
    document = Document(
        text="La situación crítica empeoró.",
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "La",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                                "start": 0,
                                "end": 2,
                            },
                            {
                                "id": 2,
                                "text": "situación",
                                "lemma": "situación",
                                "upos": "NOUN",
                                "head": 4,
                                "deprel": "nsubj",
                                "start": 3,
                                "end": 12,
                            },
                            {
                                "id": 3,
                                "text": "crítica",
                                "lemma": "crítico",
                                "upos": "ADJ",
                                "head": 2,
                                "deprel": "amod",
                                "start": 13,
                                "end": 20,
                            },
                            {
                                "id": 4,
                                "text": "empeoró",
                                "lemma": "empeorar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                                "start": 21,
                                "end": 28,
                            },
                            {
                                "id": 5,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 4,
                                "deprel": "punct",
                                "start": 28,
                                "end": 29,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = CopularPredicationRelationExtractor()

    extractor.extract(document)

    assert document.relations == []