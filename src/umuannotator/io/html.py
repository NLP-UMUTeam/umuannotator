from __future__ import annotations

import sys


def write_html_output(
    html: str,
    output_path: str,
) -> None:
    if output_path == "-":
        sys.stdout.write(html)
        return

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)