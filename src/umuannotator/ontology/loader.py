# src/umuannotator/ontology/loader.py

from rdflib import Graph


def load_ontology(path: str) -> Graph:
    graph = Graph()
    graph.parse(path)
    return graph 