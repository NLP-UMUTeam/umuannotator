from html import escape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from umuannotator.renderers.colors import collect_layers, layer_color


def render_html(data: dict, title: str = "UMU Annotator") -> str:
    css = load_css()
    custom_colors = data.get("metadata", {}).get("layer_colors", {})

    documents = [
        prepare_document(document, custom_colors)
        for document in data.get("documents", [])
    ]

    env = Environment(
        loader=FileSystemLoader(template_dir()),
        autoescape=select_autoescape(["html", "xml"]),
    )

    template = env.get_template("report.html")
    layers = collect_layers(data)

    return template.render(
        title=title,
        css=css,
        documents=documents,
        layers=layers,
        layer_color=lambda layer: layer_color(layer, custom_colors),
    )


def template_dir() -> Path:
    return Path(__file__).parent / "templates"


def load_css() -> str:
    return (template_dir() / "style.css").read_text(encoding="utf-8")


def prepare_document(document: dict, custom_colors: dict | None = None) -> dict:
    annotations = document.get("annotations", [])

    return {
        "text": document.get("text", ""),
        "annotated_text": render_annotated_text(
            document.get("text", ""),
            resolve_overlaps(annotations),
            custom_colors,
        ),
        "annotations": annotations,
        "metadata": document.get("metadata", {}),
        "tfidf_extended": sorted(
            document.get("metadata", {})
            .get("tfidf_extended", {})
            .items(),
            key=lambda item: item[1],
            reverse=True,
        ),
    }


def render_annotated_text(
    text: str,
    annotations: list[dict],
    custom_colors: dict | None = None,
) -> str:
    annotations = sorted(annotations, key=lambda a: a["start"])

    chunks = []
    cursor = 0

    for annotation in annotations:
        start = annotation["start"]
        end = annotation["end"]

        if start < cursor:
            continue

        chunks.append(escape(text[cursor:start]))

        layer = annotation.get("layer", "unknown")
        label = annotation.get("label", "")
        color = layer_color(layer, custom_colors)

        span_text = escape(text[start:end])
        title = escape(f"{label} · {layer}")

        chunks.append(
            f'<span class="annotation" '
            f'style="background:{color}" '
            f'title="{title}">{span_text}</span>'
        )

        cursor = end

    chunks.append(escape(text[cursor:]))

    return "".join(chunks)


def resolve_overlaps(annotations: list[dict]) -> list[dict]:
    candidates = sorted(
        annotations,
        key=lambda a: (
            -(a["end"] - a["start"]),
            a["start"],
        ),
    )

    selected = []

    for annotation in candidates:
        if not overlaps_any(annotation, selected):
            selected.append(annotation)

    return sorted(selected, key=lambda a: a["start"])


def overlaps_any(annotation: dict, selected: list[dict]) -> bool:
    return any(
        annotation["start"] < other["end"]
        and other["start"] < annotation["end"]
        for other in selected
    )