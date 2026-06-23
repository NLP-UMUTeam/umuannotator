import re
from pathlib import Path
from typing import Any

import yaml

from umuannotator.document.model import Annotation, Document


class RegexAnnotator:
    def __init__(
        self,
        source: str,
        layer: str = "regex",
        ignore_case: bool = True,
    ):
        self.source = source
        self.layer = layer
        self.ignore_case = ignore_case
        self.patterns = self._load_patterns(source)

    def annotate(self, document: Document) -> Document:
        flags = re.IGNORECASE if self.ignore_case else 0

        for pattern in self.patterns:
            label = pattern["label"]
            regex = pattern["regex"]
            metadata = pattern.get("metadata", {})

            for match in re.finditer(regex, document.text, flags=flags):
                document.add_annotation(
                    Annotation(
                        start=match.start(),
                        end=match.end(),
                        text=match.group(),
                        label=label,
                        layer=self.layer,
                        source=self.source,
                        type="regex",
                        subtype=metadata.get("category"),
                        metadata=metadata,
                    )
                )

        return document

    def _load_patterns(self, source: str) -> list[dict[str, Any]]:
        with Path(source).open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return data.get("patterns", [])