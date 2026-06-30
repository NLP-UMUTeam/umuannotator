from __future__ import annotations

from importlib.resources import files
from typing import Any

import yaml


def load_language_resource(
    language: str,
    name: str,
) -> dict[str, Any]:
    normalized_language = language.lower().split("-")[0]

    path = (
        files("umuannotator.resources.lang")
        / normalized_language
        / f"{name}.yml"
    )

    if not path.is_file():
        return {}

    return yaml.safe_load(
        path.read_text(encoding="utf-8"),
    ) or {}