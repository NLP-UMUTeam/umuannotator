from rdflib import RDF, RDFS, OWL, Namespace

from .model import Concept


def short_name(uri) -> str:
    """
    Return the local, human-readable name of an RDF URI.

    This is useful for display and debugging, but it should not be used
    as a stable identifier because different namespaces may contain the
    same local name.
    """
    value = str(uri)

    if "#" in value:
        return value.rsplit("#", 1)[-1]

    return value.rsplit("/", 1)[-1]


def build_index(
    graph,
    config: dict | None = None,
) -> dict[str, Concept]:
    """
    Build an ontology concept index from an RDF/OWL graph.

    The returned dictionary is indexed by concept URI, not by short name.

    Design notes
    ------------
    ``Concept.uri`` is the stable identifier used internally by the
    annotator, graph builder and semantic scoring components.

    ``Concept.name`` is a short readable name derived from the URI and
    should only be used for display, labels and debugging.

    The index can include ontology classes, named individuals, or both,
    depending on:

        ontology.entity_types.include

    Annotation properties such as regex, code, category and priority are
    configured through:

        ontology.annotation_properties
    """

    config = config or {}

    ontology_config = config.get("ontology", config)
    annotation_properties = ontology_config.get(
        "annotation_properties",
        {
            "regex": "regex",
            "code": "code",
            "category": "category",
            "priority": "priority",
        },
    )


    include_types = set(
        ontology_config
        .get("entity_types", {})
        .get("include", ["owl:Class"])
    )

    concepts: dict[str, Concept] = {}

    subjects: list[tuple[object, str]] = []

    if "owl:Class" in include_types:
        subjects.extend(
            (subject, "owl:Class")
            for subject in graph.subjects(RDF.type, OWL.Class)
        )

    if "owl:NamedIndividual" in include_types:
        subjects.extend(
            (subject, "owl:NamedIndividual")
            for subject in graph.subjects(RDF.type, OWL.NamedIndividual)
        )

    for subject, entity_type in subjects:
        uri = str(subject)
        name = short_name(subject)

        concept = Concept(
            uri=uri,
            name=name,
            entity_type=entity_type,
        )

        for label in graph.objects(subject, RDFS.label):
            concept.labels.append(str(label))

        for alias in graph.objects(subject, RDFS.seeAlso):
            concept.aliases.append(str(alias))

        for parent in graph.objects(subject, RDFS.subClassOf):
            concept.parents.append(short_name(parent))
            concept.parent_uris.append(str(parent))

        for key, property_name in annotation_properties.items():
            predicate = _resolve_annotation_property(
                graph=graph,
                subject_uri=uri,
                property_name=property_name,
            )

            values = [
                str(value)
                for value in graph.objects(subject, predicate)
            ]

            if not values:
                continue

            concept.metadata[key] = (
                values
                if len(values) > 1
                else values[0]
            )

            if key == "regex":
                concept.patterns.extend(values)

        concept.metadata["entity_type"] = entity_type
        concept.metadata["uri"] = uri
        concept.metadata["name"] = name

        concepts[uri] = concept


    return concepts


def _resolve_annotation_property(
    graph,
    subject_uri: str,
    property_name: str,
):
    """
    Resolve an ontology annotation property.

    The preferred resolution strategy searches existing predicates in
    the RDF graph by local name. This avoids assuming that annotation
    properties always live in the same namespace as the concept.

    As a fallback, the property is resolved against the subject namespace.
    This preserves compatibility with simple ontologies such as the pizza
    example, where custom properties live next to the ontology entities.
    """
    for predicate in graph.predicates():
        if short_name(predicate) == property_name:
            return predicate

    namespace = Namespace(
        subject_uri.rsplit("#", 1)[0] + "#"
    )

    return namespace[property_name]