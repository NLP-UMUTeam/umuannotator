from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
from tqdm import tqdm


def text_hash(
    text: str,
    *,
    language: str,
    processors: str,
) -> str:
    value = f"{language}\n{processors}\n{text}"
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def stanza_doc_to_dict(doc) -> dict[str, Any]:
    tokens = []
    entities = []

    for sentence in doc.sentences:
        for token in sentence.tokens:
            word = token.words[0]

            tokens.append(
                {
                    "text": token.text,
                    "start": token.start_char,
                    "end": token.end_char,
                    "lemma": word.lemma,
                    "upos": word.upos,
                    "xpos": word.xpos,
                    "feats": word.feats,
                    "deprel": word.deprel,
                    "head": word.head,
                }
            )

    for entity in doc.ents:
        entities.append(
            {
                "text": entity.text,
                "start": entity.start_char,
                "end": entity.end_char,
                "type": entity.type,
            }
        )

    return {
        "tokens": tokens,
        "entities": entities,
    }


def build_stanza_cache(
    *,
    input_path: str,
    output_path: str,
    text_column: str = "text",
    sep: str = ",",
    language: str = "es",
    processors: str = "tokenize,pos,lemma,ner",
    limit: int | None = None,
) -> None:
    import stanza

    df = pd.read_csv(input_path, sep=sep)

    if limit is not None:
        df = df.head(limit)

    nlp = stanza.Pipeline(
        lang=language,
        processors=processors,
        tokenize_no_ssplit=True,
    )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as f:
        for idx, row in tqdm(
            df.iterrows(),
            total=len(df),
            desc="Preprocessing with Stanza",
        ):
            text = str(row[text_column])
            doc = nlp(text)

            payload = {
                "doc_id": int(idx),
                "text": text,
                "text_hash": text_hash(
                    text,
                    language=language,
                    processors=processors,
                ),
                "language": language,
                "processors": processors,
                **stanza_doc_to_dict(doc),
            }

            f.write(json.dumps(payload, ensure_ascii=False) + "\n")