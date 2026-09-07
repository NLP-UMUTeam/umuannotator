from umuannotator.document import Annotation, Corpus, Document
from umuannotator.metrics.extended_tfidf import ExtendedTfidfScorer
from umuannotator.ontology.graph import build_graph
from umuannotator.ontology.loader import load_ontology


HAWAIAN = "http://example.org/pizza#HawaianPizza"
MARGHERITA = "http://example.org/pizza#MargheritaPizza"
MOZZARELLA = "http://example.org/pizza#Mozzarella"
PIZZA = "http://example.org/pizza#Pizza"


def score_with(config):
    rdf_graph = load_ontology("resources/pizza_rich.owl")
    ontology_graph = build_graph(rdf_graph, config)

    document = Document(
        text="pizza hawaiana",
        annotations=[
            Annotation(
                start=0,
                end=14,
                text="pizza hawaiana",
                label="HawaianPizza",
                layer="ontology",
                source="test",
                type="ontology",
                score=1.0,
                metadata={"concept_id": HAWAIAN},
            )
        ],
    )

    corpus = Corpus(documents=[document])

    corpus = ExtendedTfidfScorer(
        ontology_graph=ontology_graph,
        decay=0.5,
        max_distance=10,
        aggregation="sum",
    ).score(corpus)

    return corpus.documents[0].metadata["tfidf_extended"]


def test_has_ingredient_child_to_parent_does_not_activate_other_pizzas():
    config = {
        "ontology": {
            "relations": [
                {
                    "property": "rdfs:subClassOf",
                    "distance": 1,
                    "direction": "child_to_parent",
                },
                {
                    "property": "hasIngredient",
                    "distance": 2,
                    "direction": "child_to_parent",
                },
            ]
        }
    }

    scores = score_with(config)

    assert HAWAIAN in scores
    assert PIZZA in scores
    assert MOZZARELLA in scores
    assert MARGHERITA not in scores


def test_has_ingredient_both_activates_related_pizzas():
    config = {
        "ontology": {
            "relations": [
                {
                    "property": "rdfs:subClassOf",
                    "distance": 1,
                    "direction": "child_to_parent",
                },
                {
                    "property": "hasIngredient",
                    "distance": 1,
                    "direction": "both",
                },
            ]
        }
    }

    scores = score_with(config)

    assert HAWAIAN in scores
    assert MOZZARELLA in scores
    assert MARGHERITA in scores


def test_has_ingredient_both_with_larger_distance_weakens_related_pizzas():
    config = {
        "ontology": {
            "relations": [
                {
                    "property": "rdfs:subClassOf",
                    "distance": 1,
                    "direction": "child_to_parent",
                },
                {
                    "property": "hasIngredient",
                    "distance": 3,
                    "direction": "both",
                },
            ]
        }
    }

    scores = score_with(config)

    assert MARGHERITA in scores
    assert scores[MARGHERITA] < scores[PIZZA]