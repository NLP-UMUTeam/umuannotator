from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from umuannotator.document.model import Document


def text_hash(
    text: str,
    *,
    language: str,
    processors: str,
    tokenize_no_ssplit: bool = True,
) -> str:
    value = (
        f"{language}\n"
        f"{processors}\n"
        f"{tokenize_no_ssplit}\n"
        f"{text}"
    )

    return hashlib.sha1(
        value.encode("utf-8")
    ).hexdigest()


class StanzaPreprocessor:
    def __init__(
        self,
        language: str = "es",
        processors: str = "tokenize,pos,lemma,ner",
        cache_dir: str = ".cache/stanza",
        use_cache: bool = True,
        metadata_key: str = "stanza",
        tokenize_no_ssplit: bool = True,
    ):
        self.language = language
        self.processors = processors
        self.cache_dir = Path(cache_dir)
        self.use_cache = use_cache
        self.metadata_key = metadata_key
        self.tokenize_no_ssplit = tokenize_no_ssplit

        self.nlp = None

        if self.use_cache:
            self.cache_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

    def process_document(
        self,
        document: Document,
    ) -> Document:
        key = text_hash(
            document.text,
            language=self.language,
            processors=self.processors,
            tokenize_no_ssplit=self.tokenize_no_ssplit,
        )

        cache_path = self._cache_path(key)

        if (
            self.use_cache
            and cache_path.exists()
        ):
            document.metadata[self.metadata_key] = (
                self._load(cache_path)
            )

            return document

        item = self._run_stanza(
            document.text
        )

        item["text_hash"] = key
        item["language"] = self.language
        item["processors"] = self.processors
        item["tokenize_no_ssplit"] = (
            self.tokenize_no_ssplit
        )

        document.metadata[
            self.metadata_key
        ] = item

        if self.use_cache:
            self._save(
                cache_path,
                item,
            )

        return document

    def _run_stanza(
        self,
        text: str,
    ) -> dict[str, Any]:
        doc = self._pipeline()(text)

        tokens = []
        sentences = []
        entities = []

        for sentence_id, sentence in enumerate(
            doc.sentences
        ):
            sentence_words = []
            sentence_tokens = []

            for token in sentence.tokens:
                token_item = {
                    "text": token.text,
                    "start": token.start_char,
                    "end": token.end_char,
                }

                sentence_tokens.append(
                    token_item
                )

                # Mantener la vista plana antigua
                # para compatibilidad.
                if token.words:
                    first_word = token.words[0]

                    tokens.append(
                        {
                            "text": token.text,
                            "start": token.start_char,
                            "end": token.end_char,
                            "lemma": first_word.lemma,
                            "upos": first_word.upos,
                            "xpos": first_word.xpos,
                            "feats": first_word.feats,
                            "deprel": first_word.deprel,
                            "head": first_word.head,
                            "sentence_id": sentence_id,
                            "word_id": first_word.id,
                        }
                    )

                for word in token.words:
                    sentence_words.append(
                        {
                            "id": word.id,
                            "text": word.text,
                            "start": token.start_char,
                            "end": token.end_char,
                            "lemma": word.lemma,
                            "upos": word.upos,
                            "xpos": word.xpos,
                            "feats": word.feats,
                            "head": word.head,
                            "deprel": word.deprel,
                        }
                    )

            sentence_start = None
            sentence_end = None

            if sentence.tokens:
                sentence_start = (
                    sentence.tokens[0].start_char
                )
                sentence_end = (
                    sentence.tokens[-1].end_char
                )

            sentences.append(
                {
                    "id": sentence_id,
                    "start": sentence_start,
                    "end": sentence_end,
                    "text": (
                        text[sentence_start:sentence_end]
                        if (
                            sentence_start is not None
                            and sentence_end is not None
                        )
                        else ""
                    ),
                    "tokens": sentence_tokens,
                    "words": sentence_words,
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
            "sentences": sentences,
            "entities": entities,
        }

    def _pipeline(self):
        if self.nlp is None:
            import stanza

            self.nlp = stanza.Pipeline(
                lang=self.language,
                processors=self.processors,
                tokenize_no_ssplit=(
                    self.tokenize_no_ssplit
                ),
            )

        return self.nlp

    def _cache_path(
        self,
        key: str,
    ) -> Path:
        return (
            self.cache_dir
            / self.language
            / self.processors.replace(
                ",",
                "_",
            )
            / key[:2]
            / f"{key}.json"
        )

    def _load(
        self,
        path: Path,
    ) -> dict[str, Any]:
        with path.open(
            encoding="utf-8"
        ) as f:
            return json.load(f)

    def _save(
        self,
        path: Path,
        item: dict[str, Any],
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                item,
                f,
                ensure_ascii=False,
            )