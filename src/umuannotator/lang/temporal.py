from __future__ import annotations

from dataclasses import dataclass

from umuannotator.lang.loader import load_language_resource


@dataclass(frozen=True)
class TemporalLanguageRules:
    bad_starts: set[str]
    bad_single_words: set[str]
    bad_prepositional_time_words: set[str]
    bad_year_surfaces: set[str]
    person_name_month_words: set[str]


EMPTY_TEMPORAL_RULES = TemporalLanguageRules(
    bad_starts=set(),
    bad_single_words=set(),
    bad_prepositional_time_words=set(),
    bad_year_surfaces=set(),
    person_name_month_words=set(),
)


def get_temporal_rules(language: str) -> TemporalLanguageRules:
    data = load_language_resource(
        language,
        "temporal",
    )

    if not data:
        return EMPTY_TEMPORAL_RULES

    return TemporalLanguageRules(
        bad_starts=set(data.get("bad_starts", [])),
        bad_single_words=set(data.get("bad_single_words", [])),
        bad_prepositional_time_words=set(
            data.get("bad_prepositional_time_words", []),
        ),
        bad_year_surfaces=set(data.get("bad_year_surfaces", [])),
        person_name_month_words=set(
            data.get("person_name_month_words", []),
        ),
    )