import requests

from umuannotator.document.model import Annotation, Document


class DBpediaSpotlightAnnotator:
    layer = "entity-linking"

    def __init__(
        self,
        language: str = "es",
        confidence: float = 0.5,
        support: int = 20,
    ):
        self.language = language
        self.confidence = confidence
        self.support = support
        self.endpoint = f"https://api.dbpedia-spotlight.org/{language}/annotate"

    def annotate(self, document: Document) -> Document:
        response = requests.get(
            self.endpoint,
            params={
                "text": document.text,
                "confidence": self.confidence,
                "support": self.support,
            },
            headers={
                "Accept": "application/json",
            },
            timeout=30,
        )

        if response.status_code != 200:
            return document

        data = response.json()

        for resource in data.get("Resources", []):
            surface = resource.get("@surfaceForm", "")
            uri = resource.get("@URI")
            offset = int(resource.get("@offset", -1))

            if offset < 0:
                continue

            document.add_annotation(
                Annotation(
                    start=offset,
                    end=offset + len(surface),
                    text=surface,
                    label=resource.get("@types", "DBPEDIA"),
                    layer=self.layer,
                    source="dbpedia-spotlight",
                    type="entity-linking",
                    subtype="dbpedia",
                    metadata={
                        "uri": uri,
                        "similarity_score": resource.get("@similarityScore"),
                        "percentage_of_second_rank": resource.get(
                            "@percentageOfSecondRank"
                        ),
                        "types": resource.get("@types"),
                    },
                )
            )

        return document