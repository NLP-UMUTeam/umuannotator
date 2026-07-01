from umuannotator.serialization.profiles import apply_output_profile


def test_full_profile_keeps_complete_data():
    data = {
        "documents": [
            {
                "text": "Pedro viaja hoy.",
                "metadata": {
                    "doc_id": "1",
                    "stanza": {
                        "tokens": [
                            {
                                "text": "Pedro",
                                "upos": "PROPN",
                            }
                        ]
                    },
                    "source": {
                        "headline": "Pedro viaja hoy.",
                    },
                },
                "annotations": [
                    {
                        "start": 0,
                        "end": 5,
                        "text": "Pedro",
                        "label": "PER",
                        "layer": "ner",
                        "source": "stanza",
                        "type": "ner",
                        "metadata": {
                            "language": "es",
                        },
                    }
                ],
            }
        ],
        "metadata": {
            "layer_colors": {
                "ner": "#eadcf8",
            },
            "timings": {
                "annotation": 1.23,
            },
        },
    }

    result = apply_output_profile(
        data,
        profile="full",
    )

    assert result == data
    assert result is not data


def test_compact_profile_removes_heavy_document_metadata():
    data = {
        "documents": [
            {
                "text": "Pedro viaja hoy.",
                "metadata": {
                    "doc_id": "1",
                    "stanza": {
                        "tokens": [
                            {
                                "text": "Pedro",
                            }
                        ]
                    },
                    "source": {
                        "headline": "Pedro viaja hoy.",
                    },
                },
                "annotations": [],
            }
        ]
    }

    result = apply_output_profile(
        data,
        profile="compact",
    )

    assert result["documents"][0]["metadata"] == {
        "doc_id": "1",
    }


def test_compact_profile_keeps_core_annotation_fields():
    data = {
        "documents": [
            {
                "text": "Hoy.",
                "annotations": [
                    {
                        "start": 0,
                        "end": 3,
                        "text": "Hoy",
                        "label": "DATE",
                        "layer": "temporal",
                        "source": "duckling-temporal",
                        "type": "temporal",
                        "subtype": None,
                        "extra": "remove-me",
                        "metadata": {
                            "normalized": "2026-06-30",
                            "grain": "day",
                            "raw_value": {
                                "value": "2026-06-30",
                            },
                            "stanza": {
                                "upos": "NOUN",
                            },
                        },
                    }
                ],
            }
        ]
    }

    result = apply_output_profile(
        data,
        profile="compact",
    )

    annotation = result["documents"][0]["annotations"][0]

    assert annotation == {
        "start": 0,
        "end": 3,
        "text": "Hoy",
        "label": "DATE",
        "layer": "temporal",
        "source": "duckling-temporal",
        "type": "temporal",
        "metadata": {
            "normalized": "2026-06-30",
            "grain": "day",
        },
    }


def test_compact_profile_keeps_layer_colors():
    data = {
        "documents": [],
        "metadata": {
            "layer_colors": {
                "temporal": "#d6e4ff",
            },
            "timings": {
                "annotation": 1.0,
            },
        },
    }

    result = apply_output_profile(
        data,
        profile="compact",
    )

    assert result["metadata"] == {
        "layer_colors": {
            "temporal": "#d6e4ff",
        }
    }


def test_unknown_profile_raises_value_error():
    data = {
        "documents": [],
    }

    try:
        apply_output_profile(
            data,
            profile="unknown",
        )
    except ValueError as error:
        assert "Unsupported output profile" in str(error)
    else:
        raise AssertionError("Expected ValueError")