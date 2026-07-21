<p align="center">
  <img src="docs/umuannotator-logo.png" alt="UMUAnnotator logo" width="500"/>
</p>

# UMUAnnotator

UMUAnnotator is a modular annotation framework for enriching text with semantic, linguistic and structured information.

It is designed around configurable annotation pipelines: preprocessors, annotators, conflict resolution, metrics, serialization and rendering can be combined from YAML configuration files and executed from the command line.

The project is mainly intended for research workflows, corpus exploration, annotation prototyping and ontology-based text analysis.

---

## Features

- Configuration-driven annotation pipelines using YAML.
- Ontology-based semantic annotation with OWL/RDF.
- Pattern-based annotation using YAML rules, regexes and phrases.
- Temporal annotation using Duckling.
- Quantity annotation using Duckling and optional Stanza preprocessing.
- Linguistic preprocessing with Stanza and local cache.
- Named Entity Recognition with Stanza.
- Global annotation conflict resolution.
- Output profiles: `compact` and `full`.
- Input formats: CSV, JSONL and plain text.
- Annotation output formats: JSON, JSONL and text.
- Metrics:
  - corpus summary
  - TF-IDF annotation salience
  - ontology-aware TF-IDF-e salience
  - salience explanation for individual concepts
- Metrics output formats:
  - console
  - JSON
  - CSV
  - HTML
- Console and HTML rendering for annotated documents.
- Interactive shell for testing configurations on individual texts.
- Unix-style pipelines using stdin/stdout.

---

## Installation

```bash
pip install -e .
```

Some optional annotators require external services or models. For example:

- Duckling must be available when using temporal, quantity or Duckling-based annotators.
- Stanza models must be installed when using Stanza preprocessing or Stanza NER.

---

## Quick start

Run a configured annotation pipeline over a CSV file:

```bash
mkdir -p outputs

umuannotator run \
  --config configs/pizza_rich.yml \
  --input datasets/pizza_es.csv \
  --input-format csv \
  --text-column text \
  --output outputs/pizza_rich.jsonl \
  --output-format jsonl \
  --output-profile compact \
  --no-progress
```

Render annotated documents as HTML:

```bash
umuannotator run \
  --config configs/pizza_rich.yml \
  --input datasets/pizza_es.csv \
  --input-format csv \
  --text-column text \
  --output - \
  --output-format jsonl \
  --output-profile full \
  --no-progress \
| umuannotator render html \
    --input - \
    --input-format jsonl \
    --output outputs/pizza_rich.html \
    --title "Pizza Rich"
```

For metrics, JSONL compact output is usually enough:

```bash
umuannotator run \
  --config configs/news.yml \
  --input ~/umuannotator-runs/news_10k/headlines_10k.csv \
  --input-format csv \
  --text-column headline \
  --output ~/umuannotator-runs/news_10k/full_compact.jsonl \
  --output-format jsonl \
  --output-profile compact \
  --no-progress
```

---

## Interactive shell

The shell is useful for testing a configuration quickly without creating input files.

```bash
umuannotator shell --config configs/pizza_rich.yml
```

Example session:

```text
UMUAnnotator shell
Type text to annotate.
Commands: :quit, :exit, :json, :table

umuannotator> Quiero una pizza familiar con masa fina y doble queso, sin piña.
```

Switch output mode inside the shell:

```text
:json
:table
:quit
```

The shell uses the same configuration, preprocessors, annotators and resolver as `umuannotator run`.

---

## Input formats

UMUAnnotator can read from files or from standard input.

Supported input formats:

```text
csv
jsonl
text
```

When possible, formats are inferred from file extensions. When reading from stdin, specify the input format explicitly.

Example with stdin:

```bash
echo '{"text":"El Gobierno anuncia ayudas hoy."}' \
| umuannotator run \
    --config configs/news.yml \
    --input - \
    --input-format jsonl \
    --output - \
    --output-format jsonl \
    --no-progress
```

---

## Output formats

For annotated corpora, `umuannotator run` supports:

```text
json
jsonl
text
```

Examples:

```bash
umuannotator run \
  --config configs/news.yml \
  --input headlines.csv \
  --input-format csv \
  --text-column headline \
  --output outputs/news.jsonl \
  --output-format jsonl
```

```bash
umuannotator run \
  --config configs/news.yml \
  --input headlines.csv \
  --input-format csv \
  --text-column headline \
  --output outputs/news.json \
  --output-format json
```

### Output profiles

UMUAnnotator supports two output profiles:

```text
compact
full
```

`compact` keeps the most useful fields for downstream processing and metrics.

`full` keeps all available metadata, including richer preprocessor and annotator data.

Example:

```bash
umuannotator run \
  --config configs/news.yml \
  --input headlines.csv \
  --input-format csv \
  --text-column headline \
  --output outputs/news_full.jsonl \
  --output-format jsonl \
  --output-profile full
```

---

## Configuration overview

A typical configuration has this structure:

```yaml
preprocessors:
  - name: stanza
    processors: tokenize,pos,lemma,ner
    cache_dir: .cache/stanza
    use_cache: true
    metadata_key: stanza

ontology:
  path: resources/news_es.owl
  language: es

annotators:
  - name: ontology
    color: "#ffd6d6"

  - name: pattern
    layer: pattern
    source: resources/patterns/news_es.yml
    color: "#e2f7d4"

  - name: stanza-ner
    layer: ner
    color: "#eadcf8"

  - name: temporal
    layer: temporal
    color: "#d6e4ff"

  - name: quantity
    layer: cantidades
    color: "#fff2cc"

resolver:
  enabled: true
  strategy: longest_non_overlapping
```

---

## PatternAnnotator

`PatternAnnotator` loads YAML rule files and supports regex and phrase matching.

Example resource:

```yaml
name: pizza_order_patterns
language: es

defaults:
  layer: pedido
  type: order_attribute
  match: regex
  case_sensitive: false
  word_boundaries: false
  priority: 0
  metadata:
    domain: pizza

patterns:
  - id: size_small
    label: SIZE_SMALL
    pattern: '\b(pequeña|pequeño|individual)\b'
    metadata:
      category: size

  - id: size_large
    label: SIZE_LARGE
    pattern: '\b(grande|familiar|tamaño familiar)\b'
    priority: 5
    metadata:
      category: size

  - id: extra_cheese
    label: EXTRA_CHEESE
    match: phrase
    pattern:
      - extra de queso
      - doble queso
      - mucho queso
    metadata:
      category: modifier
```

The official pattern format supports:

```text
name
language
defaults
patterns
pattern / patterns
regex / phrase
priority
metadata
exceptions
case_sensitive
word_boundaries
```

Use it from a pipeline configuration:

```yaml
annotators:
  - name: pattern
    layer: pedido
    source: resources/patterns/pizza_es.yml
    color: "#ffe0b2"
```

---

## Annotation conflict resolution

The resolver is an explicit phase after annotation.

Example:

```yaml
resolver:
  enabled: true
  strategy: longest_non_overlapping
```

The current resolver strategy keeps a non-overlapping set of annotations, preferring longer spans according to the selected strategy.

This is useful when several annotators or rules produce overlapping candidates.

---

## Metrics

UMUAnnotator provides corpus-level metrics over annotated documents.

The two main commands are:

```bash
umuannotator metrics summary
umuannotator metrics salience
```

Metrics can read annotated JSON or JSONL files, including stdin.

---

## Corpus summary

`metrics summary` gives descriptive counts over an annotated corpus.

Example:

```bash
umuannotator metrics summary \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --top 20
```

Typical sections include:

```text
overview
by_layer
by_label
by_layer_label
top_annotations
```

### Summary as JSON

```bash
umuannotator metrics summary \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --top 20 \
  --output-format json \
  --output outputs/summary.json
```

### Summary as CSV

CSV output is section-based:

```bash
umuannotator metrics summary \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --top 20 \
  --section by_layer \
  --output-format csv \
  --output outputs/summary_by_layer.csv
```

Overview CSV:

```bash
umuannotator metrics summary \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --section overview \
  --output-format csv \
  --output outputs/summary_overview.csv
```

### Summary as HTML

```bash
umuannotator metrics summary \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --top 20 \
  --output-format html \
  --output outputs/summary.html
```

Single-section HTML:

```bash
umuannotator metrics summary \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --top 20 \
  --section by_layer \
  --output-format html \
  --output outputs/summary_by_layer.html
```

---

## Annotation salience

`metrics salience` computes a global ranking of relevant annotations in an annotated corpus.

It tries to answer:

```text
Which annotations are most informative or characteristic in this corpus?
```

It supports two methods:

```text
tfidf
tfidf-e
```

---

## TF-IDF salience

The default method uses TF, DF, IDF and TF-IDF over annotations.

```bash
umuannotator metrics salience \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --method tfidf \
  --top 20
```

The metrics are:

| Metric | Meaning |
|---|---|
| `TF` | Total number of occurrences in the corpus |
| `DF` | Number of documents containing the annotation |
| `IDF` | Document-level rarity |
| `score` | `TF * IDF` |

The smoothed IDF formula is:

```text
idf = log((N + 1) / (df + 1)) + 1
```

where:

```text
N  = total number of documents
df = documents containing the annotation
```

### Canonical key

Annotations are grouped using a canonical key.

The current priority is:

```text
1. metadata.concept_uri
2. metadata.wikidata
3. metadata.normalized + metadata.unit
4. metadata.normalized + metadata.grain
5. metadata.normalized
6. lowercased surface text
```

Example:

```json
{
  "text": "Gobierno",
  "layer": "ontology",
  "label": "Government",
  "metadata": {
    "concept_uri": "http://example.org/news-es#Government"
  }
}
```

Canonical key:

```text
concept_uri:http://example.org/news-es#Government
```

---

## TF-IDF-e salience

`tfidf-e` extends TF-IDF using ontology relations.

It can propagate salience through an ontology graph using a configurable maximum distance, decay and direction.

Example:

```bash
umuannotator metrics salience \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --method tfidf-e \
  --ontology resources/news_es.owl \
  --max-distance 2 \
  --decay 0.5 \
  --direction both \
  --top 20
```

The output includes:

```text
score
observed_score
expanded_score
expanded_from
```

Meaning:

| Field | Meaning |
|---|---|
| `observed_score` | Direct TF-IDF score from observed annotations |
| `expanded_score` | Score received from related ontology concepts |
| `score` | Total score |
| `expanded_from` | Concepts that contributed through expansion |

Available directions:

```text
outgoing
incoming
both
```

---

## Explain salience

For TF-IDF-e, individual concepts can be inspected with `--explain`.

```bash
umuannotator metrics salience \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --method tfidf-e \
  --ontology resources/news_es.owl \
  --max-distance 2 \
  --decay 0.5 \
  --direction both \
  --explain TrafficAccident
```

JSON output:

```bash
umuannotator metrics salience \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --method tfidf-e \
  --ontology resources/news_es.owl \
  --max-distance 2 \
  --decay 0.5 \
  --direction both \
  --explain TrafficAccident \
  --output-format json \
  --output outputs/explain_traffic_accident.json
```

---

## Salience output formats

### Console

```bash
umuannotator metrics salience \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --method tfidf \
  --top 20
```

### JSON

```bash
umuannotator metrics salience \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --method tfidf \
  --top 20 \
  --output-format json \
  --output outputs/salience.json
```

### CSV

```bash
umuannotator metrics salience \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --method tfidf \
  --top 20 \
  --output-format csv \
  --output outputs/salience.csv
```

### HTML

```bash
umuannotator metrics salience \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --method tfidf \
  --top 50 \
  --output-format html \
  --output outputs/salience.html
```

TF-IDF-e HTML:

```bash
umuannotator metrics salience \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --method tfidf-e \
  --ontology resources/news_es.owl \
  --max-distance 2 \
  --decay 0.5 \
  --direction both \
  --top 50 \
  --output-format html \
  --output outputs/salience_tfidfe.html
```

---

## Filtering salience

Filter by layer:

```bash
umuannotator metrics salience \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --layer ontology \
  --top 20
```

Filter by label:

```bash
umuannotator metrics salience \
  --input outputs/news.jsonl \
  --input-format jsonl \
  --label DATE \
  --top 20
```

---

## Unix-style pipelines

`run`, `render` and `metrics` can be combined using stdin/stdout.

Run and calculate salience:

```bash
umuannotator run \
  --config configs/news.yml \
  --input headlines.csv \
  --input-format csv \
  --text-column headline \
  --output - \
  --output-format jsonl \
  --output-profile compact \
  --no-progress \
| umuannotator metrics salience \
    --input - \
    --input-format jsonl \
    --method tfidf \
    --top 20
```

Run and render HTML:

```bash
umuannotator run \
  --config configs/pizza_rich.yml \
  --input datasets/pizza_es.csv \
  --input-format csv \
  --text-column text \
  --output - \
  --output-format jsonl \
  --output-profile full \
  --no-progress \
| umuannotator render html \
    --input - \
    --input-format jsonl \
    --output outputs/pizza_rich.html \
    --title "Pizza Rich"
```

---

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

---


## Python usage

UMUAnnotator can also be used from Python. The programmatic API is currently oriented to research and experimentation, and may still evolve.

For most use cases, prefer `run_from_config`, which mirrors the CLI behavior.

### Ejemplo 1: usar run_from_config
Este es el más estable porque reutiliza exactamente el CLI:

```
from umuannotator.pipeline.runner import run_from_config
from umuannotator.io.output import write_output

data = run_from_config(
    config_path="configs/news.yml",
    input_path="headlines.csv",
    input_format="csv",
    text_column="headline",
    show_progress=False,
)

write_output(
    data,
    "outputs/news.jsonl",
    output_format="jsonl",
    output_profile="compact",
)
```

### Ejemplo 2: anotar un texto suelto

```
from umuannotator.config.loader import load_config
from umuannotator.document.model import Document
from umuannotator.pipeline.runner import build_pipeline_from_config
from umuannotator.resolution.resolver import (
    apply_resolver_if_enabled,
    resolver_config_from_dict,
)
from umuannotator.serialization.documents import serialize_document

config = load_config("configs/news.yml")
pipeline, _context = build_pipeline_from_config(config)
resolver_config = resolver_config_from_dict(config.get("resolver"))

document = Document(
    text="El Real Madrid ganó al Barcelona.",
    metadata={},
)

document = pipeline.run_document(document)

document.annotations = apply_resolver_if_enabled(
    document.annotations,
    config=resolver_config,
)

serialized = serialize_document(
    document,
    output_profile="compact",
)

print(serialized)
```

---


## Project structure

```text
umuannotator/
├── annotators/
├── cli/
├── config/
├── document/
├── io/
├── lang/
├── metrics/
│   └── output/
├── ontology/
├── pipeline/
├── preprocessors/
├── renderers/
├── resolution/
├── resources/
└── serialization/
```

---

## Development checks

Run tests:

```bash
pytest -q
```

Check for likely unused code:

```bash
vulture src/umuannotator --min-confidence 80 --exclude "*/__pycache__/*"
```

Remove Python caches:

```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -name "*.pyc" -delete
```

---

## Current status

UMUAnnotator is under active development.

The architecture is stable enough for experimentation and research workflows. The tool is suitable for iterative annotation experiments, ontology prototyping, corpus exploration and metrics generation.

It should still be considered a research-oriented tool rather than a fully stable public API.

Current priorities include:

```text
- clearer configuration validation
- more regression tests with real corpora
- improved documentation
- better handling of raw vs resolved annotations
- larger-scale streaming workflows
```

---

## License

MIT License