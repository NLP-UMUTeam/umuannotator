from __future__ import annotations

from typing import Any


class PreprocessorFactory:
    def create(
        self,
        name: str,
        *,
        language: str = "es",
        **kwargs: Any,
    ):
        if name == "stanza":
            from umuannotator.preprocessors.stanza import StanzaPreprocessor

            return StanzaPreprocessor(
                language=kwargs.get("language", language),
                processors=kwargs.get("processors", "tokenize,pos,lemma,ner"),
                cache_dir=kwargs.get("cache_dir", ".cache/stanza"),
                use_cache=kwargs.get("use_cache", True),
                metadata_key=kwargs.get("metadata_key", "stanza"),
            )

        raise ValueError(f"Unknown preprocessor: {name}")


def build_preprocessors(
    configs: list,
    *,
    language: str = "es",
):
    factory = PreprocessorFactory()
    preprocessors = []

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

        preprocessors.append(
            factory.create(
                name,
                language=language,
                **params,
            )
        )

    return preprocessors