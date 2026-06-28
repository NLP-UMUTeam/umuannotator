from pathlib import Path

from umuannotator.pipeline.runner import run_from_config

def test_run_from_config_with_csv_input(tmp_path):
    owl_path = tmp_path / "food.owl"
    config_path = tmp_path / "config.yml"
    csv_path = tmp_path / "data.csv"

    owl_path.write_text(
        """<?xml version="1.0"?>
<rdf:RDF
    xmlns="http://example.org/food#"
    xml:base="http://example.org/food"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
    xmlns:owl="http://www.w3.org/2002/07/owl#">

  <owl:Ontology rdf:about="http://example.org/food"/>

  <owl:AnnotationProperty rdf:about="http://example.org/food#regex"/>

  <owl:Class rdf:about="http://example.org/food#Pizza">
    <rdfs:label>pizza</rdfs:label>
    <regex>pizza|pizzas</regex>
  </owl:Class>

</rdf:RDF>
""",
        encoding="utf-8",
    )

    config_path.write_text(
        f"""
ontology:
  path: {owl_path}
  language: en

  entity_types:
    include:
      - owl:Class

  annotation_properties:
    regex: regex

annotators:
  - name: ontology
    color: "#ffd6d6"

resolver:
  enabled: false

metrics:
  tfidf:
    enabled: false

  extended_tfidf:
    enabled: false
""",
        encoding="utf-8",
    )

    csv_path.write_text(
        "text\nI like pizza\n",
        encoding="utf-8",
    )

    data = run_from_config(
        config_path=str(config_path),
        input_path=str(csv_path),
        input_format="csv",
        text_column="text",
        show_progress=False,
    )

    assert data["metadata"]["documents"] == 1
    assert data["metadata"]["annotations"] >= 1

    annotations = data["documents"][0]["annotations"]

    assert annotations[0]["text"].lower() == "pizza"
    assert annotations[0]["label"] == "Pizza"
    assert annotations[0]["layer"] == "ontology"


def test_run_from_config_with_jsonl_input(tmp_path):
    owl_path = tmp_path / "food.owl"
    config_path = tmp_path / "config.yml"
    jsonl_path = tmp_path / "data.jsonl"

    owl_path.write_text(
        """<?xml version="1.0"?>
<rdf:RDF
    xmlns="http://example.org/food#"
    xml:base="http://example.org/food"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
    xmlns:owl="http://www.w3.org/2002/07/owl#">

  <owl:Ontology rdf:about="http://example.org/food"/>

  <owl:Class rdf:about="http://example.org/food#Pizza">
    <rdfs:label>pizza</rdfs:label>
  </owl:Class>

</rdf:RDF>
""",
        encoding="utf-8",
    )

    config_path.write_text(
        f"""
ontology:
  path: {owl_path}
  language: en

  entity_types:
    include:
      - owl:Class

annotators:
  - name: ontology

resolver:
  enabled: false

metrics:
  tfidf:
    enabled: false

  extended_tfidf:
    enabled: false
""",
        encoding="utf-8",
    )

    jsonl_path.write_text(
        '{"id": "doc-1", "text": "I like pizza"}\n',
        encoding="utf-8",
    )

    data = run_from_config(
        config_path=str(config_path),
        input_path=str(jsonl_path),
        input_format="jsonl",
        text_column="text",
        id_column="id",
        show_progress=False,
    )

    document = data["documents"][0]

    assert document["metadata"]["doc_id"] == "doc-1"
    assert document["annotations"][0]["text"].lower() == "pizza"