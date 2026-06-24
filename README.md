# UMUAnnotator

UMUAnnotator is a modular annotation framework for enriching text with semantic, linguistic and structured information.

The project is designed around independent annotators that can be combined into annotation pipelines and executed from the command line, Python code or future web services.

## Features

* Ontology-based semantic annotation (OWL/RDF)
* Temporal annotation using Duckling
* Named Entity Recognition (Stanza)
* Dictionary and regex-based annotation
* Annotation conflict resolution
* TF-IDF and ontology-aware TF-IDF expansion
* JSON, console and HTML rendering
* Configuration-driven pipelines using YAML

## Installation

```bash
pip install -e .
```

## Quick start

Annotate a text:

```bash
umuannotator annotate \
  --text "Ayer comí una pizza hawaiana"
```

Run a complete pipeline from a configuration file:

```bash
umuannotator run \
  --config configs/pizza_rich.yml \
  --input datasets/pizza_es.csv \
  --output outputs/results.json
```

## Ontology utilities

Show ontology statistics:

```bash
umuannotator ontology info \
  --config configs/pizza_rich.yml
```

List ontology concepts:

```bash
umuannotator ontology concepts \
  --config configs/pizza_rich.yml
```

Inspect semantic distances:

```bash
umuannotator ontology distances \
  --config configs/pizza_rich.yml \
  --concept HawaianPizza
```

Inspect generated graph relations:

```bash
umuannotator ontology relations \
  --config configs/pizza_rich.yml
```

## Project structure

```text
umuannotator/
├── annotators/
├── ontology/
├── metrics/
├── renderers/
├── document/
├── pipeline/
└── cli/
```

## Core concepts

### Annotation

All annotators generate a common annotation format:

```python
Annotation(
    start=0,
    end=10,
    text="pizza hawaiana",
    label="HawaianPizza",
    layer="ontology",
)
```

### Document

Annotations are attached to documents:

```python
Document(
    text="Ayer comí una pizza hawaiana"
)
```

### Corpus

Multiple documents can be processed together:

```python
Corpus(
    documents=[...]
)
```

## Status

UMUAnnotator is under active development.

The architecture is stable enough for experimentation and research workflows, while additional annotators, metrics and ontology features continue to be added.

## License

MIT License
