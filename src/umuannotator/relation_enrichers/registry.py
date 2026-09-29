from __future__ import annotations

from typing import Any


class RelationEnricherFactory:
    def create(
        self,
        name: str,
        *,
        language: str = "es",
        **kwargs: Any,
    ):
        if name == "annotation-overlap":
            from umuannotator.relation_enrichers.annotation_overlap import (
                AnnotationOverlapRelationEnricher,
            )

            return AnnotationOverlapRelationEnricher(
                match=kwargs.get(
                    "match",
                    [
                        "exact",
                        "contained",
                    ],
                ),
            )

        raise ValueError(
            f"Unknown relation enricher: {name}"
        )


def build_relation_enrichers(
    configs: list,
    *,
    language: str = "es",
):
    factory = RelationEnricherFactory()

    relation_enrichers = []

    for item in configs:
        if isinstance(item, str):
            name = item
            params = {}
        else:
            name = item["name"]
            params = {
                key: value
                for key, value in item.items()
                if key != "name"
            }

        relation_enrichers.append(
            factory.create(
                name,
                language=language,
                **params,
            )
        )

    return relation_enrichers