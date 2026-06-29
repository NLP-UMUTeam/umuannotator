import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from umuannotator.document.model import Annotation, Document


MatchType = Literal["regex", "phrase"]
ConflictStrategy = Literal["all", "longest", "priority", "longest_priority"]


@dataclass(frozen=True)
class PatternRule:
    id: str
    label: str
    match: MatchType
    patterns: list[str]
    layer: str
    type: str
    subtype: str | None = None
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    exceptions: list[str] = field(default_factory=list)
    case_sensitive: bool | None = None
    word_boundaries: bool | None = None


@dataclass(frozen=True)
class PatternCandidate:
    start: int
    end: int
    text: str
    matched_value: str
    rule: PatternRule


class PatternAnnotator:
    def __init__(
        self,
        source: str,
        layer: str = "pattern",
        ignore_case: bool = True,
        word_boundaries: bool = True,
        conflict_strategy: ConflictStrategy = "longest_priority",
    ):
        self.source = source
        self.layer = layer
        self.ignore_case = ignore_case
        self.word_boundaries = word_boundaries
        self.conflict_strategy = conflict_strategy

        config = self._load_config(source)
        self.defaults = config.get("defaults", {}) or {}
        self.rules = self._load_rules(config)
        self._compiled = self._compile_rules(self.rules)

    def annotate(self, document: Document) -> Document:
        candidates: list[PatternCandidate] = []

        for rule, compiled_patterns in self._compiled:
            for pattern_text, regex in compiled_patterns:
                for match in regex.finditer(document.text):
                    candidate = PatternCandidate(
                        start=match.start(),
                        end=match.end(),
                        text=match.group(),
                        matched_value=pattern_text,
                        rule=rule,
                    )

                    if not self._is_excepted(document.text, candidate):
                        candidates.append(candidate)

        candidates = self._resolve_conflicts(candidates)

        for candidate in candidates:
            document.add_annotation(self._to_annotation(candidate))

        return document

    def _load_config(self, source: str) -> dict[str, Any]:
        with Path(source).open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _load_rules(self, config: dict[str, Any]) -> list[PatternRule]:
        raw_patterns = config.get("patterns", [])
        defaults = config.get("defaults", {}) or {}

        return [
            self._build_rule(raw, defaults, index)
            for index, raw in enumerate(raw_patterns)
        ]

    def _build_rule(
        self,
        raw: dict[str, Any],
        defaults: dict[str, Any],
        index: int,
    ) -> PatternRule:
        match_type = raw.get("match", defaults.get("match", "phrase"))
        patterns = self._extract_patterns(raw)

        if match_type not in {"regex", "phrase"}:
            raise ValueError(f"Unsupported match type: {match_type}")

        return PatternRule(
            id=raw.get("id", f"rule_{index}"),
            label=raw["label"],
            match=match_type,
            patterns=patterns,
            layer=raw.get("layer", defaults.get("layer", self.layer)),
            type=raw.get("type", defaults.get("type", match_type)),
            subtype=raw.get("subtype", defaults.get("subtype")),
            priority=int(raw.get("priority", defaults.get("priority", 0))),
            metadata=raw.get("metadata", {}) or {},
            exceptions=raw.get("exceptions", []) or [],
            case_sensitive=raw.get(
                "case_sensitive",
                defaults.get("case_sensitive"),
            ),
            word_boundaries=raw.get(
                "word_boundaries",
                defaults.get("word_boundaries"),
            ),
        )

    def _extract_patterns(self, raw: dict[str, Any]) -> list[str]:
        if "pattern" in raw:
            return [str(raw["pattern"])]

        if "patterns" in raw:
            values = raw["patterns"]
            if isinstance(values, str):
                return [values]
            return [str(value) for value in values]

        raise ValueError(f"Pattern rule without 'pattern' or 'patterns': {raw}")

    def _compile_rules(
        self,
        rules: list[PatternRule],
    ) -> list[tuple[PatternRule, list[tuple[str, re.Pattern[str]]]]]:
        compiled = []

        for rule in rules:
            compiled_patterns = []

            for pattern in rule.patterns:
                regex_text = self._to_regex(pattern, rule)
                flags = self._flags_for_rule(rule)
                regex = re.compile(regex_text, flags=flags)
                compiled_patterns.append((pattern, regex))

            compiled.append((rule, compiled_patterns))

        return compiled

    def _flags_for_rule(self, rule: PatternRule) -> int:
        case_sensitive = rule.case_sensitive

        if case_sensitive is None:
            ignore_case = self.ignore_case
        else:
            ignore_case = not case_sensitive

        return re.IGNORECASE if ignore_case else 0

    def _to_regex(self, pattern: str, rule: PatternRule) -> str:
        if rule.match == "regex":
            return pattern

        escaped = re.escape(pattern)

        word_boundaries = (
            self.word_boundaries
            if rule.word_boundaries is None
            else rule.word_boundaries
        )

        if word_boundaries:
            return rf"(?<!\w){escaped}(?!\w)"

        return escaped

    def _is_excepted(self, text: str, candidate: PatternCandidate) -> bool:
        if not candidate.rule.exceptions:
            return False

        flags = self._flags_for_rule(candidate.rule)

        for exception in candidate.rule.exceptions:
            exception_regex = re.compile(
                rf"(?<!\w){re.escape(exception)}(?!\w)",
                flags=flags,
            )

            for match in exception_regex.finditer(text):
                if self._overlaps(
                    candidate.start,
                    candidate.end,
                    match.start(),
                    match.end(),
                ):
                    return True

        return False

    def _resolve_conflicts(
        self,
        candidates: list[PatternCandidate],
    ) -> list[PatternCandidate]:
        if self.conflict_strategy == "all":
            return sorted(candidates, key=lambda c: (c.start, c.end))

        if self.conflict_strategy == "longest":
            return self._select_non_overlapping(
                candidates,
                key=lambda c: (c.end - c.start, -c.start),
            )

        if self.conflict_strategy == "priority":
            return self._select_non_overlapping(
                candidates,
                key=lambda c: (c.rule.priority, c.end - c.start, -c.start),
            )

        if self.conflict_strategy == "longest_priority":
            return self._select_non_overlapping(
                candidates,
                key=lambda c: (c.end - c.start, c.rule.priority, -c.start),
            )

        raise ValueError(f"Unsupported conflict strategy: {self.conflict_strategy}")

    def _select_non_overlapping(
        self,
        candidates: list[PatternCandidate],
        key,
    ) -> list[PatternCandidate]:
        selected: list[PatternCandidate] = []

        for candidate in sorted(candidates, key=key, reverse=True):
            overlaps_existing = any(
                self._overlaps(
                    candidate.start,
                    candidate.end,
                    existing.start,
                    existing.end,
                )
                for existing in selected
            )

            if not overlaps_existing:
                selected.append(candidate)

        return sorted(selected, key=lambda c: (c.start, c.end))

    def _overlaps(
        self,
        start_a: int,
        end_a: int,
        start_b: int,
        end_b: int,
    ) -> bool:
        return start_a < end_b and start_b < end_a

    def _to_annotation(self, candidate: PatternCandidate) -> Annotation:
        rule = candidate.rule

        metadata = {
            **rule.metadata,
            "rule_id": rule.id,
            "matched_value": candidate.matched_value,
            "match_type": rule.match,
            "priority": rule.priority,
        }

        return Annotation(
            start=candidate.start,
            end=candidate.end,
            text=candidate.text,
            label=rule.label,
            layer=rule.layer,
            source=self.source,
            type=rule.type,
            subtype=rule.subtype,
            metadata=metadata,
        )