from __future__ import annotations

import pytest

from umuannotator.relation_enrichers.registry import (
    build_relation_enrichers,
)


def test_build_relation_enrichers_empty():
    enrichers = build_relation_enrichers(
        [],
        language="es",
    )

    assert enrichers == []


def test_build_relation_enrichers_unknown_name():
    with pytest.raises(
        ValueError,
        match="Unknown relation enricher",
    ):
        build_relation_enrichers(
            [
                {
                    "name": "unknown-enricher",
                }
            ],
            language="es",
        )

from umuannotator.relation_enrichers import (
    AnnotationOverlapRelationEnricher,
)


def test_build_annotation_overlap_enricher():
    enrichers = build_relation_enrichers(
        [
            {
                "name": "annotation-overlap",
                "match": [
                    "exact",
                    "contained",
                ],
            }
        ],
        language="es",
    )

    assert len(enrichers) == 1
    assert isinstance(
        enrichers[0],
        AnnotationOverlapRelationEnricher,
    )

    assert enrichers[0].match == [
        "exact",
        "contained",
    ]