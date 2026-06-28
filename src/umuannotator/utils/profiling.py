# src/umuannotator/utils/profiling.py

from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Iterator


@contextmanager
def timed(name: str, timings: dict[str, float]) -> Iterator[None]:
    start = perf_counter()
    yield
    timings[name] = perf_counter() - start