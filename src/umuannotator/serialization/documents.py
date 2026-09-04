from __future__ import annotations

from typing import Any

from umuannotator.document.model import Document
from umuannotator.renderers.json import document_to_dict
from umuannotator.serialization.profiles import apply_output_profile


def serialize_document(
    document: Document,
    *,
    output_profile: str = "compact",
) -> dict[str, Any]:
    data = {
        "documents": [
            document_to_dict(document),
        ],
        "metadata": {},
    }

    serialized = apply_output_profile(
        data,
        profile=output_profile,
    )

    return serialized["documents"][0]