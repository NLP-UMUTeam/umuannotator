from rdflib import RDF, RDFS, OWL

from .model import Concept


def build_index(graph):

    concepts = {}

    for subject in graph.subjects(RDF.type, OWL.Class):

        uri = str(subject)

        name = uri.split("#")[-1]

        concept = Concept(
            uri=uri,
            name=name,
        )

        for label in graph.objects(subject, RDFS.label):
            concept.labels.append(str(label))

        for alias in graph.objects(subject, RDFS.seeAlso):
            concept.aliases.append(str(alias))

        for parent in graph.objects(subject, RDFS.subClassOf):
            concept.parents.append(str(parent).split("#")[-1])

        concepts[name] = concept

    return concepts