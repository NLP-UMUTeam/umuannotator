import typer
from rich.console import Console
from rich.table import Table

from umuannotator.config.loader import load_config
from umuannotator.ontology.graph import build_graph, distances_from
from umuannotator.ontology.index import build_index
from umuannotator.ontology.loader import load_ontology

app = typer.Typer(
    help="Commands for inspecting and using ontologies."
)

console = Console()


@app.command()
def info(
    ontology_path: str | None = typer.Option(
        None,
        "--ontology",
        "-o",
        help="Path to the OWL ontology.",
    ),
    config_path: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to a YAML configuration file.",
    ),
):
    """
    Show basic ontology statistics.

    If a config file is provided, ontology settings such as entity types
    and annotation properties are read from the YAML configuration.
    """
    config = _load_optional_config(config_path)
    ontology_path = _resolve_ontology_path(
        ontology_path,
        config,
    )

    rdf_graph = load_ontology(ontology_path)
    concepts = build_index(
        rdf_graph,
        config=config,
    )


    table = Table(title="Ontology info")
    table.add_column("Metric")
    table.add_column("Value")

    table.add_row("Ontology path", ontology_path)
    table.add_row("Triples", str(len(rdf_graph)))
    table.add_row("Concepts", str(len(concepts)))
    table.add_row(
        "Configured relations",
        str(len(config.get("ontology", {}).get("relations", []))),
    )

    console.print(table)


@app.command()
def concepts(
    ontology_path: str | None = typer.Option(
        None,
        "--ontology",
        "-o",
        help="Path to the OWL ontology.",
    ),
    config_path: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to a YAML configuration file.",
    ),
):
    """
    List ontology concepts extracted from an OWL file.

    Concepts are indexed internally by URI, but the table displays both
    the human-readable name and the stable URI.
    """
    config = _load_optional_config(config_path)
    ontology_path = _resolve_ontology_path(
        ontology_path,
        config,
    )

    rdf_graph = load_ontology(ontology_path)
    concepts = build_index(
        rdf_graph,
        config=config,
    )
    

    table = Table(title="Ontology concepts")
    table.add_column("Name")
    table.add_column("Entity type")
    table.add_column("Labels")
    table.add_column("Aliases")
    table.add_column("Patterns")
    table.add_column("Parents")
    table.add_column("URI")

    for concept in concepts.values():
        table.add_row(
            concept.name,
            concept.entity_type or "",
            ", ".join(concept.labels),
            ", ".join(concept.aliases),
            ", ".join(concept.patterns),
            ", ".join(concept.parents),
            concept.uri,
        )

    console.print(table)


@app.command()
def distances(
    concept: str = typer.Option(
        ...,
        "--concept",
        "-x",
        help="Concept URI or short concept name.",
    ),
    ontology_path: str | None = typer.Option(
        None,
        "--ontology",
        "-o",
        help="Path to the OWL ontology.",
    ),
    config_path: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to a YAML configuration file.",
    ),
    max_distance: int = typer.Option(
        3,
        "--max-distance",
        "-d",
        help="Maximum semantic distance to explore.",
    ),
):
    """
    Show semantic graph distances from a concept.

    The graph is built from ontology.relations in the YAML config.
    The input concept may be either a full URI or a short concept name.
    """
    config = _load_optional_config(config_path)
    ontology_path = _resolve_ontology_path(
        ontology_path,
        config,
    )

    rdf_graph = load_ontology(ontology_path)
    concepts = build_index(
        rdf_graph,
        config=config,
    )
    ontology_graph = build_graph(
        rdf_graph,
        config,
    )

    concept_uri = _resolve_concept_uri(
        concept,
        concepts,
    )

    distances_ = distances_from(
        ontology_graph,
        concept_uri,
        max_distance=max_distance,
    )

    table = Table(title=f"Distances from {concept}")
    table.add_column("Concept")
    table.add_column("Name")
    table.add_column("Distance")

    for uri, distance in sorted(
        distances_.items(),
        key=lambda item: item[1],
    ):
        table.add_row(
            uri,
            ontology_graph.nodes[uri].get("name", ""),
            str(distance),
        )

    console.print(table)


@app.command()
def relations(
    ontology_path: str | None = typer.Option(
        None,
        "--ontology",
        "-o",
        help="Path to the OWL ontology.",
    ),
    config_path: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to a YAML configuration file.",
    ),
):
    """
    List semantic graph edges generated from configured relations.

    This is useful for validating whether YAML relation settings produce
    the expected directed graph.
    """
    config = _load_optional_config(config_path)
    ontology_path = _resolve_ontology_path(
        ontology_path,
        config,
    )

    rdf_graph = load_ontology(ontology_path)
    ontology_graph = build_graph(
        rdf_graph,
        config,
    )

    table = Table(title="Ontology graph relations")
    table.add_column("Source")
    table.add_column("Target")
    table.add_column("Property")
    table.add_column("Direction")
    table.add_column("Distance")

    for source, target, data in ontology_graph.edges(data=True):
        table.add_row(
            ontology_graph.nodes[source].get("name", source),
            ontology_graph.nodes[target].get("name", target),
            str(data.get("property", "")),
            str(data.get("direction", "")),
            str(data.get("distance", "")),
        )

    console.print(table)


def _load_optional_config(
    config_path: str | None,
) -> dict:
    """
    Load a YAML configuration file if provided.

    Commands can still work with only --ontology for simple inspection,
    but graph-based commands need ontology.relations to produce useful
    semantic distances.
    """
    if config_path is None:
        return {}

    return load_config(config_path)


def _resolve_ontology_path(
    ontology_path: str | None,
    config: dict,
) -> str:
    """
    Resolve the ontology path from CLI options or YAML config.

    CLI values take precedence over config values.
    """
    if ontology_path is not None:
        return ontology_path

    config_path = config.get("ontology", {}).get("path")

    if config_path is None:
        raise typer.BadParameter(
            "Use --ontology or provide ontology.path in --config."
        )

    return config_path


def _resolve_concept_uri(
    concept: str,
    concepts: dict,
) -> str:
    """
    Resolve a concept argument to a stable URI.

    The user may pass either:

    - a full URI
    - a short concept name such as HawaianPizza
    """
    if concept in concepts:
        return concept

    matches = [
        uri
        for uri, item in concepts.items()
        if item.name == concept
    ]

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        raise typer.BadParameter(
            f"Ambiguous concept name: {concept}"
        )

    raise typer.BadParameter(
        f"Unknown concept: {concept}"
    )