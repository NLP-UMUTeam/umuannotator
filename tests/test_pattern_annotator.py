from pathlib import Path

from umuannotator.annotators.pattern import PatternAnnotator
from umuannotator.document.model import Document


def test_pattern_accepts_pattern_as_list(tmp_path):
    source = tmp_path / "patterns.yml"
    source.write_text(
        """
name: test_patterns
language: es

defaults:
  layer: test
  type: phrase
  match: phrase
  case_sensitive: false
  word_boundaries: true

patterns:
  - id: cheese
    label: EXTRA_CHEESE
    pattern:
      - extra de queso
      - doble queso
""",
        encoding="utf-8",
    )

    annotator = PatternAnnotator(source=str(source))
    document = Document(text="Quiero doble queso.", metadata={})

    annotator.annotate(document)

    assert len(document.annotations) == 1
    assert document.annotations[0].text == "doble queso"
    assert document.annotations[0].label == "EXTRA_CHEESE"

def test_pattern_accepts_patterns_as_list(tmp_path):
    source = tmp_path / "patterns.yml"
    source.write_text(
        """
name: test_patterns
language: es

defaults:
  layer: test
  type: phrase
  match: phrase
  case_sensitive: false
  word_boundaries: true

patterns:
  - id: cheese
    label: EXTRA_CHEESE
    patterns:
      - extra de queso
      - doble queso
""",
        encoding="utf-8",
    )

    annotator = PatternAnnotator(source=str(source))
    document = Document(text="Quiero extra de queso.", metadata={})

    annotator.annotate(document)

    assert len(document.annotations) == 1
    assert document.annotations[0].text == "extra de queso"
    assert document.annotations[0].label == "EXTRA_CHEESE"

def test_pattern_merges_default_and_rule_metadata(tmp_path):
    source = tmp_path / "patterns.yml"
    source.write_text(
        """
name: test_patterns
language: es

defaults:
  layer: test
  type: phrase
  match: phrase
  metadata:
    domain: pizza

patterns:
  - id: cheese
    label: EXTRA_CHEESE
    pattern: extra de queso
    metadata:
      category: modifier
""",
        encoding="utf-8",
    )

    annotator = PatternAnnotator(source=str(source))
    document = Document(text="Quiero extra de queso.", metadata={})

    annotator.annotate(document)

    metadata = document.annotations[0].metadata

    assert metadata["domain"] == "pizza"
    assert metadata["category"] == "modifier"
    assert metadata["rule_id"] == "cheese"

import pytest


def test_pattern_config_requires_patterns_section(tmp_path):
    source = tmp_path / "patterns.yml"
    source.write_text(
        """
name: test_patterns
language: es
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="requires a 'patterns' section"):
        PatternAnnotator(source=str(source))

def test_pattern_rule_requires_label(tmp_path):
    source = tmp_path / "patterns.yml"
    source.write_text(
        """
name: test_patterns
language: es

patterns:
  - id: missing_label
    pattern: pizza
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="without 'label'"):
        PatternAnnotator(source=str(source))


def test_pattern_rule_rejects_empty_patterns(tmp_path):
    source = tmp_path / "patterns.yml"
    source.write_text(
        """
name: test_patterns
language: es

patterns:
  - id: empty
    label: EMPTY
    pattern: ""
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="no non-empty patterns"):
        PatternAnnotator(source=str(source))