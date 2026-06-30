from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from typing import Callable, TypeVar
import io

T = TypeVar("T")


def run_silent(func: Callable[[], T]) -> T:
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        return func()