from umuannotator.metrics.summary import summarize_annotations


def test_summary_counts_documents_and_annotations():
    data = {
        "documents": [
            {
                "text": "España viajará mañana.",
                "annotations": [
                    {
                        "text": "España",
                        "layer": "entity",
                        "label": "COUNTRY",
                    },
                    {
                        "text": "mañana",
                        "layer": "temporal",
                        "label": "DATE",
                    },
                ],
            },
            {
                "text": "Sin anotaciones.",
                "annotations": [],
            },
        ]
    }

    summary = summarize_annotations(data)

    assert summary["documents"] == 2
    assert summary["documents_with_annotations"] == 1
    assert summary["documents_without_annotations"] == 1
    assert summary["annotations"] == 2
    assert summary["annotations_per_document"] == 1.0


def test_summary_counts_by_layer():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "España",
                        "layer": "entity",
                        "label": "COUNTRY",
                    },
                    {
                        "text": "mañana",
                        "layer": "temporal",
                        "label": "DATE",
                    },
                    {
                        "text": "hoy",
                        "layer": "temporal",
                        "label": "DATE",
                    },
                ]
            }
        ]
    }

    summary = summarize_annotations(data)

    assert summary["by_layer"] == [
        {
            "key": "temporal",
            "count": 2,
        },
        {
            "key": "entity",
            "count": 1,
        },
    ]


def test_summary_counts_by_label():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "mañana",
                        "layer": "temporal",
                        "label": "DATE",
                    },
                    {
                        "text": "hoy",
                        "layer": "temporal",
                        "label": "DATE",
                    },
                    {
                        "text": "10 años",
                        "layer": "temporal",
                        "label": "DURATION",
                    },
                ]
            }
        ]
    }

    summary = summarize_annotations(data)

    assert summary["by_label"] == [
        {
            "key": "DATE",
            "count": 2,
        },
        {
            "key": "DURATION",
            "count": 1,
        },
    ]


def test_summary_counts_by_layer_label():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "mañana",
                        "layer": "temporal",
                        "label": "DATE",
                    },
                    {
                        "text": "hoy",
                        "layer": "temporal",
                        "label": "DATE",
                    },
                    {
                        "text": "España",
                        "layer": "entity",
                        "label": "COUNTRY",
                    },
                ]
            }
        ]
    }

    summary = summarize_annotations(data)

    assert summary["by_layer_label"] == [
        {
            "layer": "temporal",
            "label": "DATE",
            "count": 2,
        },
        {
            "layer": "entity",
            "label": "COUNTRY",
            "count": 1,
        },
    ]


def test_summary_counts_top_annotations_by_text_layer_and_label():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "hoy",
                        "layer": "temporal",
                        "label": "DATE",
                    },
                    {
                        "text": "hoy",
                        "layer": "temporal",
                        "label": "DATE",
                    },
                    {
                        "text": "hoy",
                        "layer": "other",
                        "label": "TOKEN",
                    },
                ]
            }
        ]
    }

    summary = summarize_annotations(data)

    assert summary["top_annotations"] == [
        {
            "text": "hoy",
            "layer": "temporal",
            "label": "DATE",
            "count": 2,
        },
        {
            "text": "hoy",
            "layer": "other",
            "label": "TOKEN",
            "count": 1,
        },
    ]


def test_summary_respects_top_limit():
    data = {
        "documents": [
            {
                "annotations": [
                    {
                        "text": "a",
                        "layer": "x",
                        "label": "A",
                    },
                    {
                        "text": "b",
                        "layer": "y",
                        "label": "B",
                    },
                ]
            }
        ]
    }

    summary = summarize_annotations(
        data,
        top=1,
    )

    assert len(summary["by_layer"]) == 1
    assert len(summary["by_label"]) == 1
    assert len(summary["by_layer_label"]) == 1
    assert len(summary["top_annotations"]) == 1