import pytest

from umuannotator.relation_extractors.registry import (
    RelationExtractorFactory,
    build_relation_extractors,
)


def test_build_empty_relation_extractors():
    extractors = build_relation_extractors(
        [],
        language="es",
    )

    assert extractors == []


def test_unknown_relation_extractor():
    factory = RelationExtractorFactory()

    with pytest.raises(
        ValueError,
        match="Unknown relation extractor",
    ):
        factory.create(
            "unknown",
            language="es",
        )