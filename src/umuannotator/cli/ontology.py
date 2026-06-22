import typer
from rich.console import Console
from rich.table import Table

from umuannotator.ontology.loader import load_ontology
from umuannotator.ontology.index import build_index
from umuannotator.ontology.graph import build_graph, distances_from

app = typer.Typer(
    help="Commands for inspecting and using ontologies."
)

console = Console()


@app.command()
def info(
    ontology_path: str = typer.Option(..., "--ontology", "-o"),
):
    graph = load_ontology(ontology_path)
    concepts = build_index(graph)

    table = Table(title="Ontology info")
    table.add_column("Metric")
    table.add_column("Value")

    table.add_row("Triples", str(len(graph)))
    table.add_row("Concepts", str(len(concepts)))

    console.print(table)


@app.command()
def concepts(
    ontology_path: str = typer.Option(..., "--ontology", "-o"),
):
    graph = load_ontology(ontology_path)
    concepts = build_index(graph)

    table = Table(title="Ontology concepts")
    table.add_column("Concept")
    table.add_column("Labels")
    table.add_column("Aliases")
    table.add_column("Parents")

    for concept in concepts.values():
        table.add_row(
            concept.name,
            ", ".join(concept.labels),
            ", ".join(concept.aliases),
            ", ".join(concept.parents),
        )

    console.print(table)


@app.command()
def distances(
    ontology_path: str = typer.Option(..., "--ontology", "-o"), 
    concept: str = typer.Option(..., "--concept", "-c"),
    max_distance: int = typer.Option(3, "--max-distance", "-d"),
):
    graph = load_ontology(ontology_path)
    concepts = build_index(graph)
    ontology_graph = build_graph(concepts)

    distances_ = distances_from(
        ontology_graph,
        concept,
        max_distance=max_distance,
    )

    table = Table(title=f"Distances from {concept}")
    table.add_column("Concept")
    table.add_column("Distance")

    for name, distance in sorted(distances_.items(), key=lambda item: item[1]):
        table.add_row(name, str(distance))

    console.print(table)