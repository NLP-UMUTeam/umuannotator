from umuannotator.document import Document
from umuannotator.relation_extractors.stanza_dependency import (
    StanzaDependencyRelationExtractor,
)


def test_extract_simple_subject_verb_object():
    text = "El Gobierno anuncia ayudas."

    document = Document(
        text=text,
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "El",
                                "start": 0,
                                "end": 2,
                                "lemma": "el",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                            },
                            {
                                "id": 2,
                                "text": "Gobierno",
                                "start": 3,
                                "end": 11,
                                "lemma": "Gobierno",
                                "upos": "PROPN",
                                "head": 3,
                                "deprel": "nsubj",
                            },
                            {
                                "id": 3,
                                "text": "anuncia",
                                "start": 12,
                                "end": 19,
                                "lemma": "anunciar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                            },
                            {
                                "id": 4,
                                "text": "ayudas",
                                "start": 20,
                                "end": 26,
                                "lemma": "ayuda",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "obj",
                            },
                            {
                                "id": 5,
                                "text": ".",
                                "start": 26,
                                "end": 27,
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 3,
                                "deprel": "punct",
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    result = extractor.extract(document)

    assert len(result.relations) == 1

    relation = result.relations[0]

    assert relation.type == "predicate_argument"
    assert relation.predicate.text == "anuncia"
    assert relation.predicate.lemma == "anunciar"

    subject = relation.arguments[0]
    object_ = relation.arguments[1]

    assert subject.role == "subject"
    assert subject.text == "El Gobierno"

    assert object_.role == "object"
    assert object_.text == "ayudas"


def test_extract_expands_object_subtree():
    text = (
        "El Gobierno convoca "
        "el Consejo de Seguridad Nacional."
    )

    document = Document(
        text=text,
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "El",
                                "start": 0,
                                "end": 2,
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                            },
                            {
                                "id": 2,
                                "text": "Gobierno",
                                "start": 3,
                                "end": 11,
                                "upos": "PROPN",
                                "head": 3,
                                "deprel": "nsubj",
                            },
                            {
                                "id": 3,
                                "text": "convoca",
                                "start": 12,
                                "end": 19,
                                "lemma": "convocar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                            },
                            {
                                "id": 4,
                                "text": "el",
                                "start": 20,
                                "end": 22,
                                "upos": "DET",
                                "head": 5,
                                "deprel": "det",
                            },
                            {
                                "id": 5,
                                "text": "Consejo",
                                "start": 23,
                                "end": 30,
                                "upos": "PROPN",
                                "head": 3,
                                "deprel": "obj",
                            },
                            {
                                "id": 6,
                                "text": "de",
                                "start": 31,
                                "end": 33,
                                "upos": "ADP",
                                "head": 7,
                                "deprel": "case",
                            },
                            {
                                "id": 7,
                                "text": "Seguridad",
                                "start": 34,
                                "end": 43,
                                "upos": "PROPN",
                                "head": 5,
                                "deprel": "nmod",
                            },
                            {
                                "id": 8,
                                "text": "Nacional",
                                "start": 44,
                                "end": 52,
                                "upos": "ADJ",
                                "head": 7,
                                "deprel": "amod",
                            },
                            {
                                "id": 9,
                                "text": ".",
                                "start": 52,
                                "end": 53,
                                "upos": "PUNCT",
                                "head": 3,
                                "deprel": "punct",
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    result = extractor.extract(document)

    assert len(result.relations) == 1

    relation = result.relations[0]

    subject = relation.arguments[0]
    object_ = relation.arguments[1]

    assert subject.text == "El Gobierno"

    assert (
        object_.text
        == "el Consejo de Seguridad Nacional"
    )


def test_extract_negative_polarity():
    text = "El Gobierno no aprobará la ley."

    document = Document(
        text=text,
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "El",
                                "start": 0,
                                "end": 2,
                                "lemma": "el",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                            },
                            {
                                "id": 2,
                                "text": "Gobierno",
                                "start": 3,
                                "end": 11,
                                "lemma": "gobierno",
                                "upos": "PROPN",
                                "head": 4,
                                "deprel": "nsubj",
                            },
                            {
                                "id": 3,
                                "text": "no",
                                "start": 12,
                                "end": 14,
                                "lemma": "no",
                                "upos": "ADV",
                                "feats": "Polarity=Neg",
                                "head": 4,
                                "deprel": "advmod",
                            },
                            {
                                "id": 4,
                                "text": "aprobará",
                                "start": 15,
                                "end": 23,
                                "lemma": "aprobar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                            },
                            {
                                "id": 5,
                                "text": "la",
                                "start": 24,
                                "end": 26,
                                "lemma": "el",
                                "upos": "DET",
                                "head": 6,
                                "deprel": "det",
                            },
                            {
                                "id": 6,
                                "text": "ley",
                                "start": 27,
                                "end": 30,
                                "lemma": "ley",
                                "upos": "NOUN",
                                "head": 4,
                                "deprel": "obj",
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    result = extractor.extract(document)

    assert len(result.relations) == 1

    relation = result.relations[0]

    assert relation.predicate.text == "aprobará"
    assert relation.predicate.lemma == "aprobar"

    assert relation.metadata["polarity"] == "negative"

def test_extract_oblique_argument():
    text = "El Gobierno entrega ayudas a las familias."

    document = Document(
        text=text,
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "El",
                                "start": 0,
                                "end": 2,
                                "lemma": "el",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                            },
                            {
                                "id": 2,
                                "text": "Gobierno",
                                "start": 3,
                                "end": 11,
                                "lemma": "gobierno",
                                "upos": "PROPN",
                                "head": 3,
                                "deprel": "nsubj",
                            },
                            {
                                "id": 3,
                                "text": "entrega",
                                "start": 12,
                                "end": 19,
                                "lemma": "entregar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                            },
                            {
                                "id": 4,
                                "text": "ayudas",
                                "start": 20,
                                "end": 26,
                                "lemma": "ayuda",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "obj",
                            },
                            {
                                "id": 5,
                                "text": "a",
                                "start": 27,
                                "end": 28,
                                "lemma": "a",
                                "upos": "ADP",
                                "head": 7,
                                "deprel": "case",
                            },
                            {
                                "id": 6,
                                "text": "las",
                                "start": 29,
                                "end": 32,
                                "lemma": "el",
                                "upos": "DET",
                                "head": 7,
                                "deprel": "det",
                            },
                            {
                                "id": 7,
                                "text": "familias",
                                "start": 33,
                                "end": 41,
                                "lemma": "familia",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "obl:arg",
                            },
                            {
                                "id": 8,
                                "text": ".",
                                "start": 41,
                                "end": 42,
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 3,
                                "deprel": "punct",
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    result = extractor.extract(document)

    assert len(result.relations) == 1

    relation = result.relations[0]

    assert len(relation.arguments) == 3

    subject = relation.arguments[0]
    object_ = relation.arguments[1]
    oblique = relation.arguments[2]

    assert subject.role == "subject"
    assert subject.text == "El Gobierno"

    assert object_.role == "object"
    assert object_.text == "ayudas"

    assert oblique.role == "oblique_argument"
    assert oblique.text == "a las familias"
    assert oblique.metadata["deprel"] == "obl:arg"

    assert relation.metadata["polarity"] == "positive"

def test_extract_passive_relation():
    text = "La ley fue aprobada por el Congreso."

    document = Document(
        text=text,
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "La",
                                "start": 0,
                                "end": 2,
                                "lemma": "el",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                            },
                            {
                                "id": 2,
                                "text": "ley",
                                "start": 3,
                                "end": 6,
                                "lemma": "ley",
                                "upos": "NOUN",
                                "head": 4,
                                "deprel": "nsubj:pass",
                            },
                            {
                                "id": 3,
                                "text": "fue",
                                "start": 7,
                                "end": 10,
                                "lemma": "ser",
                                "upos": "AUX",
                                "head": 4,
                                "deprel": "aux:pass",
                            },
                            {
                                "id": 4,
                                "text": "aprobada",
                                "start": 11,
                                "end": 19,
                                "lemma": "aprobar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                            },
                            {
                                "id": 5,
                                "text": "por",
                                "start": 20,
                                "end": 23,
                                "lemma": "por",
                                "upos": "ADP",
                                "head": 7,
                                "deprel": "case",
                            },
                            {
                                "id": 6,
                                "text": "el",
                                "start": 24,
                                "end": 26,
                                "lemma": "el",
                                "upos": "DET",
                                "head": 7,
                                "deprel": "det",
                            },
                            {
                                "id": 7,
                                "text": "Congreso",
                                "start": 27,
                                "end": 35,
                                "lemma": "congreso",
                                "upos": "PROPN",
                                "head": 4,
                                "deprel": "obl:agent",
                            },
                            {
                                "id": 8,
                                "text": ".",
                                "start": 35,
                                "end": 36,
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 4,
                                "deprel": "punct",
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    result = extractor.extract(document)

    assert len(result.relations) == 1

    relation = result.relations[0]

    assert relation.predicate.text == "aprobada"
    assert relation.predicate.lemma == "aprobar"

    assert len(relation.arguments) == 2

    patient = relation.arguments[0]
    agent = relation.arguments[1]

    assert patient.role == "patient"
    assert patient.text == "La ley"
    assert patient.metadata["deprel"] == "nsubj:pass"

    assert agent.role == "agent"
    assert agent.text == "por el Congreso"
    assert agent.metadata["deprel"] == "obl:agent"

    assert relation.metadata["rule"] == "verb_passive_agent"
    assert relation.metadata["voice"] == "passive"
    assert relation.metadata["polarity"] == "positive"


def test_extract_coordinated_verbs_with_inherited_subject():
    text = "El Gobierno anuncia ayudas y reduce impuestos."

    document = Document(
        text=text,
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "El",
                                "start": 0,
                                "end": 2,
                                "lemma": "el",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                            },
                            {
                                "id": 2,
                                "text": "Gobierno",
                                "start": 3,
                                "end": 11,
                                "lemma": "gobierno",
                                "upos": "PROPN",
                                "head": 3,
                                "deprel": "nsubj",
                            },
                            {
                                "id": 3,
                                "text": "anuncia",
                                "start": 12,
                                "end": 19,
                                "lemma": "anunciar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                            },
                            {
                                "id": 4,
                                "text": "ayudas",
                                "start": 20,
                                "end": 26,
                                "lemma": "ayuda",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "obj",
                            },
                            {
                                "id": 5,
                                "text": "y",
                                "start": 27,
                                "end": 28,
                                "lemma": "y",
                                "upos": "CCONJ",
                                "head": 6,
                                "deprel": "cc",
                            },
                            {
                                "id": 6,
                                "text": "reduce",
                                "start": 29,
                                "end": 35,
                                "lemma": "reducir",
                                "upos": "VERB",
                                "head": 3,
                                "deprel": "conj",
                            },
                            {
                                "id": 7,
                                "text": "impuestos",
                                "start": 36,
                                "end": 45,
                                "lemma": "impuesto",
                                "upos": "NOUN",
                                "head": 6,
                                "deprel": "obj",
                            },
                            {
                                "id": 8,
                                "text": ".",
                                "start": 45,
                                "end": 46,
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 3,
                                "deprel": "punct",
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    result = extractor.extract(document)

    assert len(result.relations) == 2

    first = result.relations[0]
    second = result.relations[1]

    assert first.predicate.lemma == "anunciar"
    assert first.arguments[0].role == "subject"
    assert first.arguments[0].text == "El Gobierno"
    assert first.arguments[1].role == "object"
    assert first.arguments[1].text == "ayudas"

    assert second.predicate.lemma == "reducir"
    assert second.arguments[0].role == "subject"
    assert second.arguments[0].text == "El Gobierno"
    assert second.arguments[1].role == "object"
    assert second.arguments[1].text == "impuestos"

    assert "subject_inherited" not in first.metadata

    assert second.metadata["subject_inherited"] is True
    assert second.metadata["subject_inherited_from_word_id"] == 3

    assert first.metadata["polarity"] == "positive"
    assert second.metadata["polarity"] == "positive"


def test_extract_xcomp_with_inherited_subject():
    text = "El Gobierno quiere aprobar la ley."

    document = Document(
        text=text,
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "El",
                                "start": 0,
                                "end": 2,
                                "lemma": "el",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                            },
                            {
                                "id": 2,
                                "text": "Gobierno",
                                "start": 3,
                                "end": 11,
                                "lemma": "gobierno",
                                "upos": "PROPN",
                                "head": 3,
                                "deprel": "nsubj",
                            },
                            {
                                "id": 3,
                                "text": "quiere",
                                "start": 12,
                                "end": 18,
                                "lemma": "querer",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                            },
                            {
                                "id": 4,
                                "text": "aprobar",
                                "start": 19,
                                "end": 26,
                                "lemma": "aprobar",
                                "upos": "VERB",
                                "head": 3,
                                "deprel": "xcomp",
                            },
                            {
                                "id": 5,
                                "text": "la",
                                "start": 27,
                                "end": 29,
                                "lemma": "el",
                                "upos": "DET",
                                "head": 6,
                                "deprel": "det",
                            },
                            {
                                "id": 6,
                                "text": "ley",
                                "start": 30,
                                "end": 33,
                                "lemma": "ley",
                                "upos": "NOUN",
                                "head": 4,
                                "deprel": "obj",
                            },
                            {
                                "id": 7,
                                "text": ".",
                                "start": 33,
                                "end": 34,
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 3,
                                "deprel": "punct",
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    result = extractor.extract(document)

    assert len(result.relations) == 1

    relation = result.relations[0]

    assert relation.predicate.text == "aprobar"
    assert relation.predicate.lemma == "aprobar"

    assert len(relation.arguments) == 2

    subject = relation.arguments[0]
    object_ = relation.arguments[1]

    assert subject.role == "subject"
    assert subject.text == "El Gobierno"

    assert object_.role == "object"
    assert object_.text == "la ley"

    assert relation.metadata["subject_inherited"] is True
    assert relation.metadata["subject_inherited_from_word_id"] == 3
    assert relation.metadata["subject_inheritance"] == "xcomp_control"
    assert relation.metadata["polarity"] == "positive"

def test_extract_ccomp_relation_without_subject_inheritance():
    document = Document(
        text="El ministro afirma que aprobarán la reforma.",
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
                                "text": "ministro",
                                "lemma": "ministro",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "nsubj",
                                "start": 3,
                                "end": 11,
                            },
                            {
                                "id": 3,
                                "text": "afirma",
                                "lemma": "afirmar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                                "start": 12,
                                "end": 18,
                            },
                            {
                                "id": 4,
                                "text": "que",
                                "lemma": "que",
                                "upos": "SCONJ",
                                "head": 5,
                                "deprel": "mark",
                                "start": 19,
                                "end": 22,
                            },
                            {
                                "id": 5,
                                "text": "aprobarán",
                                "lemma": "aprobar",
                                "upos": "VERB",
                                "head": 3,
                                "deprel": "ccomp",
                                "start": 23,
                                "end": 32,
                            },
                            {
                                "id": 6,
                                "text": "la",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 7,
                                "deprel": "det",
                                "start": 33,
                                "end": 35,
                            },
                            {
                                "id": 7,
                                "text": "reforma",
                                "lemma": "reforma",
                                "upos": "NOUN",
                                "head": 5,
                                "deprel": "obj",
                                "start": 36,
                                "end": 43,
                            },
                            {
                                "id": 8,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 3,
                                "deprel": "punct",
                                "start": 43,
                                "end": 44,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()
    extractor.extract(document)

    assert len(document.relations) == 2

    matrix_relation = document.relations[0]

    assert matrix_relation.type == "predicate_argument"
    assert matrix_relation.predicate.text == "afirma"
    assert matrix_relation.predicate.lemma == "afirmar"

    assert len(matrix_relation.arguments) == 2

    assert matrix_relation.arguments[0].role == "subject"
    assert matrix_relation.arguments[0].text == "El ministro"

    assert matrix_relation.arguments[1].role == "clausal_complement"
    assert (
        matrix_relation.arguments[1].text
        == "que aprobarán la reforma"
    )

    assert matrix_relation.metadata["rule"] == "verb_nsubj_ccomp"

    embedded_relation = document.relations[1]

    assert embedded_relation.type == "predicate_argument"
    assert embedded_relation.predicate.text == "aprobarán"
    assert embedded_relation.predicate.lemma == "aprobar"

    assert len(embedded_relation.arguments) == 1

    assert embedded_relation.arguments[0].role == "object"
    assert embedded_relation.arguments[0].text == "la reforma"

    assert embedded_relation.metadata["rule"] == "verb_obj"

    assert "subject_inherited" not in embedded_relation.metadata

def test_ccomp_does_not_inherit_matrix_subject():
    text = "El ministro afirma que aprobarán la reforma."

    document = Document(
        text=text,
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "El",
                                "start": 0,
                                "end": 2,
                                "lemma": "el",
                                "upos": "DET",
                                "head": 2,
                                "deprel": "det",
                            },
                            {
                                "id": 2,
                                "text": "ministro",
                                "start": 3,
                                "end": 11,
                                "lemma": "ministro",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "nsubj",
                            },
                            {
                                "id": 3,
                                "text": "afirma",
                                "start": 12,
                                "end": 18,
                                "lemma": "afirmar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                            },
                            {
                                "id": 4,
                                "text": "que",
                                "start": 19,
                                "end": 22,
                                "lemma": "que",
                                "upos": "SCONJ",
                                "head": 5,
                                "deprel": "mark",
                            },
                            {
                                "id": 5,
                                "text": "aprobarán",
                                "start": 23,
                                "end": 32,
                                "lemma": "aprobar",
                                "upos": "VERB",
                                "head": 3,
                                "deprel": "ccomp",
                            },
                            {
                                "id": 6,
                                "text": "la",
                                "start": 33,
                                "end": 35,
                                "lemma": "el",
                                "upos": "DET",
                                "head": 7,
                                "deprel": "det",
                            },
                            {
                                "id": 7,
                                "text": "reforma",
                                "start": 36,
                                "end": 43,
                                "lemma": "reforma",
                                "upos": "NOUN",
                                "head": 5,
                                "deprel": "obj",
                            },
                            {
                                "id": 8,
                                "text": ".",
                                "start": 43,
                                "end": 44,
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 3,
                                "deprel": "punct",
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    result = extractor.extract(document)

    assert not any(
        relation.predicate.lemma == "aprobar"
        and any(
            argument.role == "subject"
            and argument.text == "El ministro"
            for argument in relation.arguments
        )
        for relation in result.relations
    )

def test_extract_relation_with_subject_only():
    document = Document(
        text="La bomba funciona.",
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
                                "text": "bomba",
                                "lemma": "bomba",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "nsubj",
                                "start": 3,
                                "end": 8,
                            },
                            {
                                "id": 3,
                                "text": "funciona",
                                "lemma": "funcionar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                                "start": 9,
                                "end": 17,
                            },
                            {
                                "id": 4,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 3,
                                "deprel": "punct",
                                "start": 17,
                                "end": 18,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()
    extractor.extract(document)

    assert len(document.relations) == 1

    relation = document.relations[0]

    assert relation.type == "predicate_argument"
    assert relation.predicate.text == "funciona"
    assert relation.predicate.lemma == "funcionar"

    assert len(relation.arguments) == 1

    assert relation.arguments[0].role == "subject"
    assert relation.arguments[0].text == "La bomba"

    assert relation.metadata["rule"] == "verb_nsubj"
    assert relation.metadata["polarity"] == "positive"


def test_extract_relation_with_object_only():
    document = Document(
        text="Cancelan la procesión.",
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "Cancelan",
                                "lemma": "cancelar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                                "start": 0,
                                "end": 8,
                            },
                            {
                                "id": 2,
                                "text": "la",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 3,
                                "deprel": "det",
                                "start": 9,
                                "end": 11,
                            },
                            {
                                "id": 3,
                                "text": "procesión",
                                "lemma": "procesión",
                                "upos": "NOUN",
                                "head": 1,
                                "deprel": "obj",
                                "start": 12,
                                "end": 21,
                            },
                            {
                                "id": 4,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 1,
                                "deprel": "punct",
                                "start": 21,
                                "end": 22,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()
    extractor.extract(document)

    assert len(document.relations) == 1

    relation = document.relations[0]

    assert relation.type == "predicate_argument"
    assert relation.predicate.text == "Cancelan"
    assert relation.predicate.lemma == "cancelar"

    assert len(relation.arguments) == 1

    assert relation.arguments[0].role == "object"
    assert relation.arguments[0].text == "la procesión"

    assert relation.metadata["rule"] == "verb_obj"
    assert relation.metadata["polarity"] == "positive"

    assert "subject_inherited" not in relation.metadata


def test_extract_infinitive_relation_with_object_only():
    document = Document(
        text="Retirar la cubierta posterior.",
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "Retirar",
                                "lemma": "retirar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                                "start": 0,
                                "end": 7,
                            },
                            {
                                "id": 2,
                                "text": "la",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 3,
                                "deprel": "det",
                                "start": 8,
                                "end": 10,
                            },
                            {
                                "id": 3,
                                "text": "cubierta",
                                "lemma": "cubierta",
                                "upos": "NOUN",
                                "head": 1,
                                "deprel": "obj",
                                "start": 11,
                                "end": 19,
                            },
                            {
                                "id": 4,
                                "text": "posterior",
                                "lemma": "posterior",
                                "upos": "ADJ",
                                "head": 3,
                                "deprel": "amod",
                                "start": 20,
                                "end": 29,
                            },
                            {
                                "id": 5,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 1,
                                "deprel": "punct",
                                "start": 29,
                                "end": 30,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()
    extractor.extract(document)

    assert len(document.relations) == 1

    relation = document.relations[0]

    assert relation.type == "predicate_argument"
    assert relation.predicate.text == "Retirar"
    assert relation.predicate.lemma == "retirar"

    assert len(relation.arguments) == 1

    assert relation.arguments[0].role == "object"
    assert relation.arguments[0].text == "la cubierta posterior"

    assert relation.metadata["rule"] == "verb_obj"
    assert relation.metadata["polarity"] == "positive"


def test_extract_passive_relation_without_agent():
    document = Document(
        text="La válvula fue sustituida.",
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
                                "text": "válvula",
                                "lemma": "válvula",
                                "upos": "NOUN",
                                "head": 4,
                                "deprel": "nsubj:pass",
                                "start": 3,
                                "end": 10,
                            },
                            {
                                "id": 3,
                                "text": "fue",
                                "lemma": "ser",
                                "upos": "AUX",
                                "head": 4,
                                "deprel": "aux:pass",
                                "start": 11,
                                "end": 14,
                            },
                            {
                                "id": 4,
                                "text": "sustituida",
                                "lemma": "sustituir",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                                "start": 15,
                                "end": 25,
                            },
                            {
                                "id": 5,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 4,
                                "deprel": "punct",
                                "start": 25,
                                "end": 26,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()
    extractor.extract(document)

    assert len(document.relations) == 1

    relation = document.relations[0]

    assert relation.type == "predicate_argument"
    assert relation.predicate.text == "sustituida"
    assert relation.predicate.lemma == "sustituir"

    assert len(relation.arguments) == 1

    assert relation.arguments[0].role == "patient"
    assert relation.arguments[0].text == "La válvula"

    assert relation.metadata["rule"] == "verb_passive"
    assert relation.metadata["voice"] == "passive"
    assert relation.metadata["polarity"] == "positive"


def test_extract_ccomp_with_subject_inherited_from_coordination():
    document = Document(
        text="Sánchez explica el problema y admite que dimitirá.",
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 0,
                        "words": [
                            {
                                "id": 1,
                                "text": "Sánchez",
                                "lemma": "Sánchez",
                                "upos": "PROPN",
                                "head": 2,
                                "deprel": "nsubj",
                                "start": 0,
                                "end": 7,
                            },
                            {
                                "id": 2,
                                "text": "explica",
                                "lemma": "explicar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                                "start": 8,
                                "end": 15,
                            },
                            {
                                "id": 3,
                                "text": "el",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 4,
                                "deprel": "det",
                                "start": 16,
                                "end": 18,
                            },
                            {
                                "id": 4,
                                "text": "problema",
                                "lemma": "problema",
                                "upos": "NOUN",
                                "head": 2,
                                "deprel": "obj",
                                "start": 19,
                                "end": 27,
                            },
                            {
                                "id": 5,
                                "text": "y",
                                "lemma": "y",
                                "upos": "CCONJ",
                                "head": 6,
                                "deprel": "cc",
                                "start": 28,
                                "end": 29,
                            },
                            {
                                "id": 6,
                                "text": "admite",
                                "lemma": "admitir",
                                "upos": "VERB",
                                "head": 2,
                                "deprel": "conj",
                                "start": 30,
                                "end": 36,
                            },
                            {
                                "id": 7,
                                "text": "que",
                                "lemma": "que",
                                "upos": "SCONJ",
                                "head": 8,
                                "deprel": "mark",
                                "start": 37,
                                "end": 40,
                            },
                            {
                                "id": 8,
                                "text": "dimitirá",
                                "lemma": "dimitir",
                                "upos": "VERB",
                                "head": 6,
                                "deprel": "ccomp",
                                "start": 41,
                                "end": 49,
                            },
                            {
                                "id": 9,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 2,
                                "deprel": "punct",
                                "start": 49,
                                "end": 50,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()
    extractor.extract(document)

    admit_relation = next(
        relation
        for relation in document.relations
        if relation.predicate.lemma == "admitir"
    )

    assert admit_relation.type == "predicate_argument"
    assert admit_relation.predicate.text == "admite"

    assert len(admit_relation.arguments) == 2

    assert admit_relation.arguments[0].role == "subject"
    assert admit_relation.arguments[0].text == "Sánchez"

    assert admit_relation.arguments[1].role == "clausal_complement"
    assert admit_relation.arguments[1].text == "que dimitirá"

    assert admit_relation.metadata["rule"] == "verb_nsubj_ccomp"
    assert admit_relation.metadata["subject_inherited"] is True
    assert (
        admit_relation.metadata["subject_inherited_from_word_id"]
        == 2
    )
    assert (
        admit_relation.metadata["subject_inheritance"]
        == "coordination"
    )

def test_extract_relation_with_indirect_object():
    document = Document(
        text="El técnico entregó la llave al supervisor.",
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
                                "text": "técnico",
                                "lemma": "técnico",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "nsubj",
                                "start": 3,
                                "end": 10,
                            },
                            {
                                "id": 3,
                                "text": "entregó",
                                "lemma": "entregar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                                "start": 11,
                                "end": 18,
                            },
                            {
                                "id": 4,
                                "text": "la",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 5,
                                "deprel": "det",
                                "start": 19,
                                "end": 21,
                            },
                            {
                                "id": 5,
                                "text": "llave",
                                "lemma": "llave",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "obj",
                                "start": 22,
                                "end": 27,
                            },
                            {
                                "id": 6,
                                "text": "al",
                                "lemma": "a",
                                "upos": "ADP",
                                "head": 7,
                                "deprel": "case",
                                "start": 28,
                                "end": 30,
                            },
                            {
                                "id": 7,
                                "text": "supervisor",
                                "lemma": "supervisor",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "iobj",
                                "start": 31,
                                "end": 41,
                            },
                            {
                                "id": 8,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 3,
                                "deprel": "punct",
                                "start": 41,
                                "end": 42,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()
    extractor.extract(document)

    assert len(document.relations) == 1

    relation = document.relations[0]

    assert relation.predicate.lemma == "entregar"

    assert [arg.role for arg in relation.arguments] == [
        "subject",
        "object",
        "indirect_object",
    ]

    assert relation.arguments[0].text == "El técnico"
    assert relation.arguments[1].text == "la llave"
    assert relation.arguments[2].text == "al supervisor"

    assert relation.metadata["rule"] == "verb_nsubj_obj"
    assert relation.metadata["polarity"] == "positive"

def test_extract_relation_with_multiple_generic_obliques():
    document = Document(
        text="El técnico reparó la bomba con una llave en el taller.",
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
                                "text": "técnico",
                                "lemma": "técnico",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "nsubj",
                                "start": 3,
                                "end": 10,
                            },
                            {
                                "id": 3,
                                "text": "reparó",
                                "lemma": "reparar",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                                "start": 11,
                                "end": 17,
                            },
                            {
                                "id": 4,
                                "text": "la",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 5,
                                "deprel": "det",
                                "start": 18,
                                "end": 20,
                            },
                            {
                                "id": 5,
                                "text": "bomba",
                                "lemma": "bomba",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "obj",
                                "start": 21,
                                "end": 26,
                            },
                            {
                                "id": 6,
                                "text": "con",
                                "lemma": "con",
                                "upos": "ADP",
                                "head": 8,
                                "deprel": "case",
                                "start": 27,
                                "end": 30,
                            },
                            {
                                "id": 7,
                                "text": "una",
                                "lemma": "uno",
                                "upos": "DET",
                                "head": 8,
                                "deprel": "det",
                                "start": 31,
                                "end": 34,
                            },
                            {
                                "id": 8,
                                "text": "llave",
                                "lemma": "llave",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "obl",
                                "start": 35,
                                "end": 40,
                            },
                            {
                                "id": 9,
                                "text": "en",
                                "lemma": "en",
                                "upos": "ADP",
                                "head": 11,
                                "deprel": "case",
                                "start": 41,
                                "end": 43,
                            },
                            {
                                "id": 10,
                                "text": "el",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 11,
                                "deprel": "det",
                                "start": 44,
                                "end": 46,
                            },
                            {
                                "id": 11,
                                "text": "taller",
                                "lemma": "taller",
                                "upos": "NOUN",
                                "head": 3,
                                "deprel": "obl",
                                "start": 47,
                                "end": 53,
                            },
                            {
                                "id": 12,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 3,
                                "deprel": "punct",
                                "start": 53,
                                "end": 54,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()
    extractor.extract(document)

    assert len(document.relations) == 1

    relation = document.relations[0]

    assert relation.predicate.lemma == "reparar"

    assert [arg.role for arg in relation.arguments] == [
        "subject",
        "object",
        "oblique",
        "oblique",
    ]

    assert relation.arguments[0].text == "El técnico"
    assert relation.arguments[1].text == "la bomba"
    assert relation.arguments[2].text == "con una llave"
    assert relation.arguments[3].text == "en el taller"

    assert relation.metadata["rule"] == "verb_nsubj_obj"
    assert relation.metadata["polarity"] == "positive"


def test_finite_predicate_with_generic_oblique_creates_relation():
    document = Document(
        text="Viajo en Cercanías.",
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 1,
                        "words": [
                            {
                                "id": 1,
                                "text": "Viajo",
                                "lemma": "viajar",
                                "upos": "VERB",
                                "feats": (
                                    "Mood=Ind|Number=Sing|"
                                    "Person=1|Tense=Pres|"
                                    "VerbForm=Fin"
                                ),
                                "head": 0,
                                "deprel": "root",
                                "start": 0,
                                "end": 5,
                            },
                            {
                                "id": 2,
                                "text": "en",
                                "lemma": "en",
                                "upos": "ADP",
                                "head": 3,
                                "deprel": "case",
                                "start": 6,
                                "end": 8,
                            },
                            {
                                "id": 3,
                                "text": "Cercanías",
                                "lemma": "Cercanías",
                                "upos": "PROPN",
                                "head": 1,
                                "deprel": "obl",
                                "start": 9,
                                "end": 18,
                            },
                            {
                                "id": 4,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 1,
                                "deprel": "punct",
                                "start": 18,
                                "end": 19,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    extractor.extract(document)

    assert len(document.relations) == 1

    relation = document.relations[0]

    assert relation.predicate.lemma == "viajar"
    assert relation.metadata["rule"] == "verb_obl"

    assert len(relation.arguments) == 1
    assert relation.arguments[0].role == "oblique"
    assert relation.arguments[0].text == "en Cercanías"

def test_another_finite_predicate_with_generic_oblique_creates_relation():
    document = Document(
        text="Dormiré en la calle.",
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 1,
                        "words": [
                            {
                                "id": 1,
                                "text": "Dormiré",
                                "lemma": "dormir",
                                "upos": "VERB",
                                "feats": (
                                    "Mood=Ind|Number=Sing|"
                                    "Person=1|Tense=Fut|"
                                    "VerbForm=Fin"
                                ),
                                "head": 0,
                                "deprel": "root",
                                "start": 0,
                                "end": 7,
                            },
                            {
                                "id": 2,
                                "text": "en",
                                "lemma": "en",
                                "upos": "ADP",
                                "head": 4,
                                "deprel": "case",
                                "start": 8,
                                "end": 10,
                            },
                            {
                                "id": 3,
                                "text": "la",
                                "lemma": "el",
                                "upos": "DET",
                                "head": 4,
                                "deprel": "det",
                                "start": 11,
                                "end": 13,
                            },
                            {
                                "id": 4,
                                "text": "calle",
                                "lemma": "calle",
                                "upos": "NOUN",
                                "head": 1,
                                "deprel": "obl",
                                "start": 14,
                                "end": 19,
                            },
                            {
                                "id": 5,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 1,
                                "deprel": "punct",
                                "start": 19,
                                "end": 20,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    extractor.extract(document)

    assert len(document.relations) == 1

    relation = document.relations[0]

    assert relation.predicate.lemma == "dormir"
    assert relation.metadata["rule"] == "verb_obl"
    assert relation.arguments[0].text == "en la calle"


def test_infinitive_with_only_generic_oblique_does_not_create_relation():
    document = Document(
        text="Viajar en tren.",
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 1,
                        "words": [
                            {
                                "id": 1,
                                "text": "Viajar",
                                "lemma": "viajar",
                                "upos": "VERB",
                                "feats": "VerbForm=Inf",
                                "head": 0,
                                "deprel": "root",
                                "start": 0,
                                "end": 6,
                            },
                            {
                                "id": 2,
                                "text": "en",
                                "lemma": "en",
                                "upos": "ADP",
                                "head": 3,
                                "deprel": "case",
                                "start": 7,
                                "end": 9,
                            },
                            {
                                "id": 3,
                                "text": "tren",
                                "lemma": "tren",
                                "upos": "NOUN",
                                "head": 1,
                                "deprel": "obl",
                                "start": 10,
                                "end": 14,
                            },
                            {
                                "id": 4,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 1,
                                "deprel": "punct",
                                "start": 14,
                                "end": 15,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    extractor.extract(document)

    assert document.relations == []


def test_finite_predicate_without_arguments_does_not_create_relation():
    document = Document(
        text="Llueve.",
        metadata={
            "stanza": {
                "sentences": [
                    {
                        "id": 1,
                        "words": [
                            {
                                "id": 1,
                                "text": "Llueve",
                                "lemma": "llover",
                                "upos": "VERB",
                                "feats": (
                                    "Mood=Ind|Number=Sing|"
                                    "Person=3|Tense=Pres|"
                                    "VerbForm=Fin"
                                ),
                                "head": 0,
                                "deprel": "root",
                                "start": 0,
                                "end": 6,
                            },
                            {
                                "id": 2,
                                "text": ".",
                                "lemma": ".",
                                "upos": "PUNCT",
                                "head": 1,
                                "deprel": "punct",
                                "start": 6,
                                "end": 7,
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    extractor.extract(document)

    assert document.relations == []