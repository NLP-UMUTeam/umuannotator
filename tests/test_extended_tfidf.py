from umuannotator.document import Annotation, Corpus, Document
from umuannotator.metrics.extended_tfidf import ExtendedTfidfScorer
from umuannotator.ontology.graph import build_graph
from umuannotator.ontology.loader import load_ontology


CONFIG = {
    "ontology": {
        "relations": [
            {
                "property": "rdfs:subClassOf",
                "distance": 1,
                "direction": "child_to_parent",
            },
            {
                "property": "rdf:type",
                "distance": 1,
                "direction": "instance_to_class",
            },
            {
                "property": "hasIngredient",
                "distance": 1,
                "direction": "both",
            },
            {
                "property": "hasCookingMethod",
                "distance": 2,
                "direction": "both",
            },
            {
                "property": "hasDietType",
                "distance": 2,
                "direction": "both",
            },
        ]
    }
}


def test_extended_tfidf_generates_parent_scores():
    rdf_graph = load_ontology("resources/pizza_rich.owl")
    ontology_graph = build_graph(rdf_graph, CONFIG)

    hawaian_uri = "http://example.org/pizza#HawaianPizza"
    pizza_uri = "http://example.org/pizza#Pizza"

    document = Document(
        text="Me gusta la pizza hawaiana",
        annotations=[
            Annotation(
                start=12,
                end=26,
                text="pizza hawaiana",
                label="HawaianPizza",
                layer="ontology",
                source="test",
                type="ontology",
                score=1.0,
                metadata={
                    "concept_id": hawaian_uri,
                    "concept_uri": hawaian_uri,
                    "concept_name": "HawaianPizza",
                },
            )
        ],
    )

    corpus = Corpus(documents=[document])

    corpus = ExtendedTfidfScorer(
        ontology_graph,
        decay=0.5,
        max_distance=5,
    ).score(corpus)

    scores = corpus.documents[0].metadata["tfidf_extended"]

    assert hawaian_uri in scores
    assert pizza_uri in scores
    assert scores[hawaian_uri] == 1.0
    assert scores[pizza_uri] == 0.5