from rdflib import RDF, RDFS, OWL
import networkx as nx


def short_name(uri) -> str:
    """
    Return the local, human-readable name of an RDF URI.

    This is used only as node metadata. Graph nodes themselves use full
    URIs to avoid collisions between concepts with the same local name.
    """
    value = str(uri)

    if "#" in value:
        return value.rsplit("#", 1)[-1]

    return value.rsplit("/", 1)[-1]


def build_graph(
    rdf_graph,
    config: dict,
):
    """
    Build a directed semantic graph from an RDF/OWL ontology.

    The graph is fully driven by:

        ontology.relations

    Example:

        ontology:
          relations:
            - property: rdfs:subClassOf
              distance: 1
              direction: child_to_parent

    Design notes
    ------------
    The graph is always a NetworkX DiGraph.

    Nodes are full RDF URI strings, not short names. This keeps the
    semantic graph stable even when different namespaces contain the
    same local name.

    Human-readable names are stored as node metadata:

        graph.nodes[uri]["name"]

    Semantic distances are stored twice on each edge:

        distance
            Domain-level meaning.

        weight
            NetworkX implementation detail used by Dijkstra.

    Bidirectional relations are represented as two directed edges.
    """
    graph = nx.DiGraph()

    ontology_config = config.get("ontology", {})
    relations = ontology_config.get("relations", [])

    for relation in relations:
        property_name = relation["property"]

        distance = relation.get(
            "distance",
            relation.get("weight", 1),
        )

        direction = relation.get(
            "direction",
            "child_to_parent",
        )

        predicate = resolve_predicate(
            rdf_graph,
            property_name,
        )

        for source, _, target in rdf_graph.triples(
            (None, predicate, None)
        ):
            
            if _should_skip_relation(
                property_name,
                target,
            ):
                continue
            
            source_uri = str(source)
            target_uri = str(target)

            _ensure_node(graph, source_uri)
            _ensure_node(graph, target_uri)

            add_relation(
                graph=graph,
                source=source_uri,
                target=target_uri,
                distance=distance,
                direction=direction,
                property_name=property_name,
            )

    return graph


def resolve_predicate(
    graph,
    property_name,
):
    """
    Resolve a configured ontology property to an RDF predicate.

    Supported explicit names:

    - rdfs:subClassOf
    - rdf:type

    Custom ontology properties are resolved by matching their local URI
    name against predicates already present in the RDF graph.

    Example:

        hasIngredient

    may resolve to:

        http://example.org/pizza#hasIngredient
    """
    if property_name == "rdfs:subClassOf":
        return RDFS.subClassOf

    if property_name == "rdf:type":
        return RDF.type

    for predicate in graph.predicates():
        if short_name(predicate) == property_name:
            return predicate

    raise ValueError(
        f"Unknown ontology property: {property_name}"
    )


def add_relation(
    graph,
    source,
    target,
    distance,
    direction,
    property_name,
):
    """
    Add one or more directed semantic edges.

    Directions
    ----------

    child_to_parent
        source -> target

        Used for triples such as:

            Child rdfs:subClassOf Parent

    parent_to_child
        target -> source

    both
        source -> target
        target -> source

        Used for associative semantic relations where propagation should
        work in both directions.

    instance_to_class
        source -> target

        Used for triples such as:

            individual rdf:type Class

    Notes
    -----
    ``distance`` is the semantic cost of traversing the relation.

    ``weight`` is kept as an alias because NetworkX Dijkstra uses that
    attribute name.
    """
    edge_metadata = {
        "weight": distance,
        "distance": distance,
        "property": property_name,
        "direction": direction,
    }

    if direction == "child_to_parent":
        _add_edge(
            graph,
            source,
            target,
            edge_metadata,
        )

    elif direction == "parent_to_child":
        _add_edge(
            graph,
            target,
            source,
            edge_metadata,
        )

    elif direction == "both":
        _add_edge(
            graph,
            source,
            target,
            edge_metadata,
        )

        _add_edge(
            graph,
            target,
            source,
            edge_metadata,
        )

    elif direction == "instance_to_class":
        _add_edge(
            graph,
            source,
            target,
            edge_metadata,
        )

    else:
        raise ValueError(
            f"Unknown direction: {direction}"
        )


def _ensure_node(
    graph,
    uri: str,
) -> None:
    """
    Add a URI node if it does not already exist.

    Node identity is the full URI. The short name is stored only for
    display and debugging.
    """
    if uri in graph:
        return

    graph.add_node(
        uri,
        uri=uri,
        name=short_name(uri),
    )


def _add_edge(
    graph,
    source: str,
    target: str,
    metadata: dict,
) -> None:
    """
    Add a directed edge and ensure both endpoint nodes exist.
    """
    _ensure_node(graph, source)
    _ensure_node(graph, target)

    graph.add_edge(
        source,
        target,
        **metadata,
    )


def distances_from(graph, concept_uri: str, max_distance: int | None = None):
    """
    Compute shortest semantic distances from a concept URI.
    """
    return dict(
        nx.single_source_dijkstra_path_length(
            graph,
            concept_uri,
            cutoff=max_distance,
            weight="weight",
        )
    )


def _should_skip_relation(
    property_name: str,
    target,
) -> bool:
    """
    Return True for ontology-internal rdf:type triples that should not
    become semantic propagation edges.

    Example skipped triples:

        Pizza rdf:type owl:Class
        hasIngredient rdf:type owl:ObjectProperty

    These describe OWL structure, not domain semantics.
    """
    if property_name != "rdf:type":
        return False

    return target in {
        OWL.Class,
        OWL.NamedIndividual,
        OWL.ObjectProperty,
        OWL.AnnotationProperty,
        RDF.Property,
    }