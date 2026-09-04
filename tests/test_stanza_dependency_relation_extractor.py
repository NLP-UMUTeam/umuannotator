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

def test_no_relation_without_object():
    text = "El Gobierno dimite."

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
                                "text": "dimite",
                                "start": 12,
                                "end": 18,
                                "lemma": "dimitir",
                                "upos": "VERB",
                                "head": 0,
                                "deprel": "root",
                            },
                        ],
                    }
                ]
            }
        },
    )

    extractor = StanzaDependencyRelationExtractor()

    result = extractor.extract(document)

    assert result.relations == []

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

    assert len(result.relations) == 1

    relation = result.relations[0]

    assert relation.predicate.text == "afirma"
    assert relation.predicate.lemma == "afirmar"

    assert len(relation.arguments) == 2

    subject = relation.arguments[0]
    complement = relation.arguments[1]

    assert subject.role == "subject"
    assert subject.text == "El ministro"

    assert complement.role == "clausal_complement"
    assert complement.text == "que aprobarán la reforma"

    assert relation.metadata["rule"] == "verb_nsubj_ccomp"
    assert relation.metadata["polarity"] == "positive"

    assert "subject_inherited" not in relation.metadata

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