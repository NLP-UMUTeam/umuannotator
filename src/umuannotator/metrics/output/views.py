from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricOutputView:
    section: str | None = None
    explain: str | None = None