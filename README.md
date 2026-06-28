<p align="center">
  <img src="docs/umuannotator-logo.png" alt="UMUAnnotator logo" width="500"/>
</p>


# UMUAnnotator

UMUAnnotator is a modular annotation framework for enriching text with semantic, linguistic and structured information.

The project is designed around independent annotators that can be combined into annotation pipelines and executed from the command line, Python code or future web services.

## Features

* Configuration-driven annotation pipelines using YAML
* Ontology-based semantic annotation with OWL/RDF
* Temporal annotation using Duckling
* Quantity annotation using Duckling + optional Stanza preprocessing
* Linguistic preprocessing with Stanza and local cache
* Named Entity Recognition with Stanza
* Dictionary and regex-based annotation
* Annotation conflict resolution
* TF-IDF and ontology-aware TF-IDF expansion
* Input formats: CSV, JSONL and plain text
* Output formats: JSON, JSONL and text
* Console and HTML rendering
* Unix-style pipelines using stdin/stdout

## Installation

```bash
pip install -e .
```

## Quick start

Run a configured annotation pipeline over a CSV file:

```bash
mkdir -p outputs

umuannotator run \
  --config configs/pizza_rich.yml \
  --input datasets/pizza_es.csv \
  --text-column text \
  --output outputs/pizza_rich.json
```

Render the result as HTML:

```
umuannotator render html \
  --input outputs/pizza_rich.json \
  --output outputs/pizza_rich.html \
  --title "Pizza Rich"
```

Or run and render in a single pipeline:

```
umuannotator run \
  --config configs/pizza_rich.yml \
  --input datasets/pizza_es.csv \
  --text-column text \
  --output - \
  --output-format json \
  --no-progress \
| umuannotator render html \
  --input - \
  --output outputs/pizza_rich.html \
  --title "Pizza Rich"
```

## Input and output formats
UMUAnnotator can read from files or from standard input: CSV, JSONL y plain text.

When input or output formats are omitted, they are inferred from file extensions when possible.



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
├── preprocessors/
├── ontology/
├── metrics/
├── renderers/
├── document/
├── pipeline/
├── io/
└── cli/
```


## Status

UMUAnnotator is under active development.

The architecture is stable enough for experimentation and research workflows, while additional annotators, metrics and ontology features continue to be added.

## License

MIT License
