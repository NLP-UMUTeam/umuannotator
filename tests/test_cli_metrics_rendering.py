from umuannotator.metrics.output.helpers import (
    format_float,
    format_percent,
    shorten_uri,
)


def test_format_float():
    assert format_float(1.23456) == "1.235"


def test_format_percent():
    assert format_percent(25, 100) == "25.0%"


def test_format_percent_handles_zero_total():
    assert format_percent(25, 0) == "0.0%"


def test_shorten_uri_with_hash():
    assert (
        shorten_uri("http://example.org/news-es#TrafficAccident")
        == "TrafficAccident"
    )


def test_shorten_uri_with_concept_uri_prefix():
    assert (
        shorten_uri(
            "concept_uri:http://example.org/news-es#TrafficAccident"
        )
        == "TrafficAccident"
    )