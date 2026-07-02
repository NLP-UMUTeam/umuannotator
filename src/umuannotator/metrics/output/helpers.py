from __future__ import annotations


def format_float(
    value,
    *,
    digits: int = 3,
) -> str:
    if value is None:
        return ""

    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def format_percent(
    part: float,
    total: float,
) -> str:
    if total <= 0:
        return "0.0%"

    return f"{(part / total) * 100:.1f}%"


def shorten_uri(value: str) -> str:
    if not value:
        return ""

    if value.startswith("concept_uri:"):
        return shorten_uri(
            value.removeprefix("concept_uri:"),
        )

    if "#" in value:
        return value.rsplit("#", 1)[-1]

    if "/" in value:
        return value.rstrip("/").rsplit("/", 1)[-1]

    return value


def normalize_explain_target(
    value: str,
) -> str:
    value = value.strip()

    if value.startswith("concept_uri:"):
        value = value.removeprefix("concept_uri:")

    return value