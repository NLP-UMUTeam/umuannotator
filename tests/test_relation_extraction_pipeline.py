from umuannotator.document import (
    Document,
    Relation,
    RelationArgument,
    RelationPredicate,
)
from umuannotator.pipeline import (
    RelationExtractionPipeline,
)


class DummyRelationExtractor:
    def extract(
        self,
        document: Document,
    ) -> Document:
        document.add_relation(
            Relation(
                type="dummy",
                predicate=RelationPredicate(
                    start=0,
                    end=5,
                    text="Pizza",
                ),
                arguments=[
                    RelationArgument(
                        role="test",
                        start=0,
                        end=5,
                        text="Pizza",
                    )
                ],
                source="dummy",
            )
        )

        return document


def test_relation_extraction_pipeline():
    pipeline = RelationExtractionPipeline(
        extractors=[
            DummyRelationExtractor(),
        ]
    )

    document = Document(
        text="Pizza"
    )

    result = pipeline.run_document(document)

    assert len(result.relations) == 1
    assert result.relations[0].type == "dummy"
    assert result.relations[0].source == "dummy"


def test_relation_extraction_pipeline_empty():
    pipeline = RelationExtractionPipeline(
        extractors=[]
    )

    document = Document(
        text="Pizza"
    )

    result = pipeline.run_document(document)

    assert result.relations == []