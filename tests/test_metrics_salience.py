from umuannotator.metrics.salience import (
    annotation_to_salience_key,
    compute_salience,
)


def test_salience_counts_tf_and_df():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "hoy",
                        "layer": "temporal",
                        "label": "DATE",
                        "metadata": {
                            "normalized": "2026-06-30",
                            "grain": "day",
                        },
                    },
                    {
                        "text": "hoy",
                        "layer": "temporal",
                        "label": "DATE",
                        "metadata": {
                            "normalized": "2026-06-30",
                            "grain": "day",
                        },
                    },
                ]
            },
            {
                "annotations": [
                    {
                        "text": "hoy",
                        "layer": "temporal",
                        "label": "DATE",
                        "metadata": {
                            "normalized": "2026-06-30",
                            "grain": "day",
                        },
                    }
                ]
            },
        ]
    }

    result = compute_salience(data, top=10)

    assert result["documents"] == 2
    assert result["items"][0]["tf"] == 3
    assert result["items"][0]["df"] == 2
    assert result["items"][0]["layer"] == "temporal"
    assert result["items"][0]["label"] == "DATE"


def test_salience_uses_concept_uri_as_canonical_key():
    annotation = {
        "text": "Gobierno",
        "layer": "ontology",
        "label": "Government",
        "metadata": {
            "concept_uri": "http://example.org/Government",
        },
    }

    key = annotation_to_salience_key(annotation)

    assert key.canonical == "concept_uri:http://example.org/Government"


def test_salience_uses_wikidata_as_canonical_key():
    annotation = {
        "text": "España",
        "layer": "entity",
        "label": "COUNTRY",
        "metadata": {
            "wikidata": "Q29",
        },
    }

    key = annotation_to_salience_key(annotation)

    assert key.canonical == "wikidata:Q29"


def test_salience_uses_normalized_and_unit_as_canonical_key():
    annotation = {
        "text": "2500 euros",
        "layer": "cantidades",
        "label": "MONEY",
        "metadata": {
            "normalized": 2500,
            "unit": "EUR",
        },
    }

    key = annotation_to_salience_key(annotation)

    assert key.canonical == "normalized:2500|unit:EUR"


def test_salience_uses_normalized_and_grain_as_canonical_key():
    annotation = {
        "text": "2026",
        "layer": "temporal",
        "label": "DATE",
        "metadata": {
            "normalized": "2026-01-01",
            "grain": "year",
        },
    }

    key = annotation_to_salience_key(annotation)

    assert key.canonical == "normalized:2026-01-01|grain:year"


def test_salience_falls_back_to_lowercase_text():
    annotation = {
        "text": "Gobierno",
        "layer": "ontology",
        "label": "Government",
        "metadata": {},
    }

    key = annotation_to_salience_key(annotation)

    assert key.canonical == "text:gobierno"


def test_salience_filters_by_layer():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "hoy",
                        "layer": "temporal",
                        "label": "DATE",
                        "metadata": {},
                    },
                    {
                        "text": "Gobierno",
                        "layer": "ontology",
                        "label": "Government",
                        "metadata": {},
                    },
                ]
            }
        ]
    }

    result = compute_salience(
        data,
        top=10,
        layer="temporal",
    )

    assert len(result["items"]) == 1
    assert result["items"][0]["layer"] == "temporal"


def test_salience_filters_by_label():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "hoy",
                        "layer": "temporal",
                        "label": "DATE",
                        "metadata": {},
                    },
                    {
                        "text": "10 años",
                        "layer": "temporal",
                        "label": "DURATION",
                        "metadata": {},
                    },
                ]
            }
        ]
    }

    result = compute_salience(
        data,
        top=10,
        label="DURATION",
    )

    assert len(result["items"]) == 1
    assert result["items"][0]["label"] == "DURATION"


def test_salience_respects_top_limit():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "a",
                        "layer": "x",
                        "label": "A",
                        "metadata": {},
                    },
                    {
                        "text": "b",
                        "layer": "x",
                        "label": "B",
                        "metadata": {},
                    },
                ]
            }
        ]
    }

    result = compute_salience(
        data,
        top=1,
    )

    assert len(result["items"]) == 1