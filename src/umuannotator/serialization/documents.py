from __future__ import annotations

from typing import Any

from umuannotator.document.model import Document
from umuannotator.serialization.profiles import apply_output_profile


def serialize_document(
    document: Document,
    *,
    output_profile: str = "compact",
) -> dict[str, Any]:
    data = {
        "documents": [
            document.to_dict(),
        ],
        "metadata": {},
    }

    serialized = apply_output_profile(
        data,
        profile=output_profile,
    )

    return serialized["documents"][0]