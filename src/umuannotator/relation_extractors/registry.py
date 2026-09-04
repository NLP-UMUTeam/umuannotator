from __future__ import annotations

from typing import Any


class RelationExtractorFactory:
    def create(
        self,
        name: str,
        *,
        language: str = "es",
        **kwargs: Any,
    ):
        if name == "stanza-dependency":
            from umuannotator.relation_extractors.stanza_dependency import (
                StanzaDependencyRelationExtractor,
            )

            return StanzaDependencyRelationExtractor(
                metadata_key=kwargs.get(
                    "metadata_key",
                    "stanza",
                ),
                source=kwargs.get(
                    "source",
                    "stanza-dependency",
                ),
            )

        raise ValueError(
            f"Unknown relation extractor: {name}"
        )


def build_relation_extractors(
    configs: list,
    *,
    language: str = "es",
):
    factory = RelationExtractorFactory()

    relation_extractors = []

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

        relation_extractors.append(
            factory.create(
                name,
                language=language,
                **params,
            )
        )

    return relation_extractors