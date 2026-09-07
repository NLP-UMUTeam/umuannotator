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