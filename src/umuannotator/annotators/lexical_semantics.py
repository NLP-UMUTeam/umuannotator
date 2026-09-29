from __future__ import annotations

from collections import deque
from collections.abc import Collection
from typing import Any

import wn

from umuannotator.document.model import Annotation, Document


STANZA_TO_WORDNET_POS = {
    "NOUN": "n",
}


class LexicalSemanticAnnotator:
    def __init__(
        self,
        *,
        language: str,
        lexicon: str,
        semantic_classes: dict[str, dict[str, Any]],
        layer: str = "lexical_semantics",
        max_hypernym_depth: int = 10,
    ):
        self.language = language
        self.lexicon = lexicon
        self.layer = layer
        self.max_hypernym_depth = max_hypernym_depth
        self.semantic_classes = semantic_classes

        self.wordnet = wn.Wordnet(self.lexicon)

        self._lookup_cache: dict[
            tuple[str, str],
            dict[str, Any],
        ] = {}

    def annotate(self, document: Document) -> Document:
        stanza = document.metadata.get("stanza")

        if not stanza:
            return document

        for token in stanza.get("tokens", []):
            self._annotate_token(
                document=document,
                token=token,
            )

        return document

    def _annotate_token(
        self,
        *,
        document: Document,
        token: dict[str, Any],
    ) -> None:
        start = token.get("start")
        end = token.get("end")
        lemma = token.get("lemma")
        upos = token.get("upos")

        if (
            start is None
            or end is None
            or not lemma
            or not upos
        ):
            return

        wordnet_pos = STANZA_TO_WORDNET_POS.get(upos)

        if wordnet_pos is None:
            return

        result = self._lookup(
            lemma=lemma,
            wordnet_pos=wordnet_pos,
        )

        semantic_classes = result["semantic_classes"]

        if not semantic_classes:
            return

        text = document.text[start:end]

        document.add_annotation(
            Annotation(
                start=start,
                end=end,
                text=text,
                label="LEXICAL_SEMANTICS",
                layer=self.layer,
                source="wordnet",
                type="lexical_semantics",
                metadata={
                    "language": self.language,
                    "lexicon": self.lexicon,
                    "lemma": lemma,
                    "upos": upos,
                    "wordnet_pos": wordnet_pos,
                    "semantic_classes": semantic_classes,
                    "synsets": result["synsets"],
                    "disambiguated": False,
                },
            )
        )

    def _lookup(
        self,
        *,
        lemma: str,
        wordnet_pos: str,
    ) -> dict[str, Any]:
        cache_key = (
            lemma.lower(),
            wordnet_pos,
        )

        cached = self._lookup_cache.get(cache_key)

        if cached is not None:
            return cached

        semantic_classes: set[str] = set()
        synset_ids: list[str] = []

        for sense in self.wordnet.senses(lemma):
            synset = sense.synset()

            if synset.pos != wordnet_pos:
                continue

            synset_ids.append(synset.id)

            classes = self._classify_synset(synset)
            semantic_classes.update(classes)

        result = {
            "semantic_classes": sorted(semantic_classes),
            "synsets": sorted(set(synset_ids)),
        }

        self._lookup_cache[cache_key] = result

        return result

    def _classify_synset(
        self,
        synset,
    ) -> set[str]:
        queue = deque(
            [
                (synset, 0),
            ]
        )

        visited: set[str] = set()
        matches: list[tuple[int, str]] = []

        while queue:
            current, depth = queue.popleft()

            if current.id in visited:
                continue

            if depth > self.max_hypernym_depth:
                continue

            visited.add(current.id)

            for semantic_class, config in self.semantic_classes.items():
                roots = config.get("roots", [])

                if current.id in roots:
                    matches.append(
                        (
                            depth,
                            semantic_class,
                        )
                    )

            if depth >= self.max_hypernym_depth:
                continue

            for hypernym in current.hypernyms():
                queue.append(
                    (
                        hypernym,
                        depth + 1,
                    )
                )

        if not matches:
            return set()

        minimum_depth = min(
            depth
            for depth, _ in matches
        )

        return {
            semantic_class
            for depth, semantic_class in matches
            if depth == minimum_depth
        }
