from dateparser.search import search_dates

from umuannotator.document.model import Annotation, Document


TRAILING_WORDS = {"a", "en", "de", "del", "la", "el"}


def clean_surface(surface: str) -> str:
    parts = surface.split()

    while len(parts) > 1 and parts[-1].lower() in TRAILING_WORDS:
        parts = parts[:-1]

    return " ".join(parts)


class TemporalAnnotator: 
    layer = "temporal"

    def __init__(self, language: str = "es"):
        self.language = language

    def annotate(self, document: Document) -> Document:

        matches = search_dates(
            document.text,
            languages=[self.language],
        )

        if not matches:
            return document

        used_offsets = set()

        for surface, value in matches:
            clean = clean_surface(surface)

            start = document.text.find(clean)

            if start < 0:
                continue

            end = start + len(clean)

            key = (start, end) 

            if key in used_offsets:
                continue

            used_offsets.add(key)

            document.add_annotation(
                Annotation(
                    start=start,
                    end=end,
                    text=clean,
                    label="DATE",
                    layer=self.layer,
                    source="dateparser",
                    type="temporal",
                    metadata={
                        "normalized": value.isoformat(),
                        "raw": surface,
                    },
                )
            )

        return document