from pathlib import Path

import yaml

from umuannotator.document import (
    Document,
    Relation,
    RelationArgument,
    RelationPredicate,
)
from umuannotator.relation_extractors.reported_speech import (
    ReportedSpeechRelationExtractor,
)


def _write_config(
    tmp_path: Path,
    lemmas: list[str],
) -> str:
    path = tmp_path / "reported_speech.yml"

    path.write_text(
        yaml.safe_dump(
            {
                "reporting_lemmas": lemmas,
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    return str(path)


def _build_ccomp_relation(
    *,
    predicate_text: str,
    predicate_lemma: str,
) -> Relation:
    return Relation(
        type="predicate_argument",
        predicate=RelationPredicate(
            start=12,
            end=18,
            text=predicate_text,
            lemma=predicate_lemma,
            metadata={
                "word_id": 3,
            },
        ),
        arguments=[
            RelationArgument(
                role="subject",
                start=0,
                end=11,
                text="El ministro",
                metadata={
                    "head_word_id": 2,
                    "deprel": "nsubj",
                },
            ),
            RelationArgument(
                role="clausal_complement",
                start=19,
                end=52,
                text="que la reforma se aprobará mañana",
                metadata={
                    "head_word_id": 8,
                    "deprel": "ccomp",
                },
            ),
        ],
        source="stanza-dependency",
        metadata={
            "sentence_id": 0,
            "rule": "verb_nsubj_ccomp",
            "polarity": "positive",
        },
    )


def test_extract_reported_speech_from_afirmar(
    tmp_path: Path,
):
    source = _write_config(
        tmp_path,
        [
            "decir",
            "afirmar",
        ],
    )

    document = Document(
        text=(
            "El ministro afirmó que "
            "la reforma se aprobará mañana."
        ),
        relations=[
            _build_ccomp_relation(
                predicate_text="afirmó",
                predicate_lemma="afirmar",
            )
        ],
    )

    extractor = ReportedSpeechRelationExtractor(
        source=source,
    )

    result = extractor.extract(document)

    assert len(result.relations) == 2

    original = result.relations[0]
    reported = result.relations[1]

    assert original.type == "predicate_argument"
    assert reported.type == "reported_speech"

    assert reported.predicate.text == "afirmó"
    assert reported.predicate.lemma == "afirmar"

    assert len(reported.arguments) == 2

    speaker = reported.arguments[0]
    content = reported.arguments[1]

    assert speaker.role == "speaker"
    assert speaker.text == "El ministro"

    assert content.role == "content"
    assert (
        content.text
        == "que la reforma se aprobará mañana"
    )

    assert reported.source == source

    assert (
        reported.metadata["derived_from"]
        == "predicate_argument"
    )

    assert (
        reported.metadata["reporting_lemma"]
        == "afirmar"
    )

    assert (
        reported.metadata["source_relation_rule"]
        == "verb_nsubj_ccomp"
    )

    assert reported.metadata["sentence_id"] == 0


def test_extract_reported_speech_from_decir(
    tmp_path: Path,
):
    source = _write_config(
        tmp_path,
        [
            "decir",
            "afirmar",
        ],
    )

    document = Document(
        text=(
            'El ministro dijo: '
            '"Aprobaremos la reforma mañana".'
        ),
        relations=[
            _build_ccomp_relation(
                predicate_text="dijo",
                predicate_lemma="decir",
            )
        ],
    )

    extractor = ReportedSpeechRelationExtractor(
        source=source,
    )

    result = extractor.extract(document)

    reported = [
        relation
        for relation in result.relations
        if relation.type == "reported_speech"
    ]

    assert len(reported) == 1
    assert reported[0].predicate.lemma == "decir"


def test_ignore_non_reporting_predicate(
    tmp_path: Path,
):
    source = _write_config(
        tmp_path,
        [
            "decir",
            "afirmar",
        ],
    )

    document = Document(
        text=(
            "El ministro piensa que "
            "la reforma se aprobará mañana."
        ),
        relations=[
            _build_ccomp_relation(
                predicate_text="piensa",
                predicate_lemma="pensar",
            )
        ],
    )

    extractor = ReportedSpeechRelationExtractor(
        source=source,
    )

    result = extractor.extract(document)

    assert len(result.relations) == 1

    assert (
        result.relations[0].type
        == "predicate_argument"
    )


def test_detect_direct_reported_speech(
    tmp_path: Path,
):
    source = _write_config(
        tmp_path,
        [
            "decir",
            "afirmar",
        ],
    )

    relation = Relation(
        type="predicate_argument",
        predicate=RelationPredicate(
            start=12,
            end=16,
            text="dijo",
            lemma="decir",
            metadata={
                "word_id": 3,
            },
        ),
        arguments=[
            RelationArgument(
                role="subject",
                start=0,
                end=11,
                text="El ministro",
                metadata={
                    "head_word_id": 2,
                    "deprel": "nsubj",
                },
            ),
            RelationArgument(
                role="clausal_complement",
                start=16,
                end=49,
                text=': "Aprobaremos la reforma mañana"',
                metadata={
                    "head_word_id": 6,
                    "deprel": "ccomp",
                },
            ),
        ],
        source="stanza-dependency",
        metadata={
            "sentence_id": 0,
            "rule": "verb_nsubj_ccomp",
            "polarity": "positive",
        },
    )

    document = Document(
        text=(
            'El ministro dijo: '
            '"Aprobaremos la reforma mañana".'
        ),
        relations=[relation],
    )

    extractor = ReportedSpeechRelationExtractor(
        source=source,
    )

    result = extractor.extract(document)

    reported = [
        relation
        for relation in result.relations
        if relation.type == "reported_speech"
    ]

    assert len(reported) == 1

    assert (
        reported[0].metadata["speech_type"]
        == "direct"
    )