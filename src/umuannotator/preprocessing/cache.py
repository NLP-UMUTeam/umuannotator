# src/umuannotator/preprocessing/cache.py

from __future__ import annotations

import json


def load_jsonl_cache(path: str) -> dict[str, dict]:
    cache = {}

    with open(path, encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            cache[item["text_hash"]] = item

    return cache