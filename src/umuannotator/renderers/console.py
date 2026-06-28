from rich.console import Console
from rich.text import Text

console = Console()

FALLBACK_COLORS = [
    "red",
    "green",
    "blue",
    "magenta",
    "cyan",
    "yellow",
    "bright_red",
    "bright_green",
    "bright_blue",
]


def fallback_color_for(value: str) -> str:
    return FALLBACK_COLORS[hash(value) % len(FALLBACK_COLORS)]


def layer_color(layer: str, layer_colors: dict[str, str]) -> str:
    return layer_colors.get(layer) or fallback_color_for(layer)


def render_document(
    document: dict,
    *,
    layer_colors: dict[str, str],
) -> None:
    text = document["text"]
    annotations = sorted(
        document.get("annotations", []),
        key=lambda ann: (ann["start"], -(ann["end"] - ann["start"])),
    )

    rich_text = Text(text)

    for ann in annotations:
        start = ann["start"]
        end = ann["end"]
        layer = ann["layer"]

        rich_text.stylize(
            f"bold {layer_color(layer, layer_colors)}",
            start,
            end,
        )

    console.print(rich_text)

    for ann in annotations:
        color = layer_color(ann["layer"], layer_colors)

        console.print(
            f"  [{color}]"
            f"{ann['text']}[/] "
            f"→ {ann['label']} "
            f"({ann['layer']})"
        )

    console.print()


def render_corpus(data: dict) -> None:
    layer_colors = (
        data.get("metadata", {})
        .get("layer_colors", {})
    )

    for index, document in enumerate(data.get("documents", []), start=1):
        console.rule(f"Document {index}")
        render_document(
            document,
            layer_colors=layer_colors,
        )