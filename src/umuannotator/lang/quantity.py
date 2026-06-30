from __future__ import annotations

from dataclasses import dataclass
import re

from umuannotator.lang.loader import load_language_resource


@dataclass(frozen=True)
class QuantityLanguageRules:
    determiner_number_words: set[str]
    multipliers: dict[str, int]
    multiplier_after_number_re: re.Pattern[str] | None


def get_quantity_rules(language: str) -> QuantityLanguageRules:
    data = load_language_resource(
        language,
        "quantity",
    )

    pattern = data.get("patterns", {}).get("multiplier_after_number")

    return QuantityLanguageRules(
        determiner_number_words=set(
            data.get("determiner_number_words", []),
        ),
        multipliers={
            str(key): int(value)
            for key, value in data.get("multipliers", {}).items()
        },
        multiplier_after_number_re=(
            re.compile(
                pattern,
                flags=re.IGNORECASE,
            )
            if pattern
            else None
        ),
    )