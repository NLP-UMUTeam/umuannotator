from rich.console import Console
from rich.text import Text

console = Console()

COLORS = [
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


def color_for(label: str) -> str:
    return COLORS[hash(label) % len(COLORS)]


def render_document(document: dict) -> None:
    text = document["text"]
    annotations = sorted(
        document.get("annotations", []),
        key=lambda ann: (ann["start"], -(ann["end"] - ann["start"])),
    )

    rich_text = Text(text)

    for ann in annotations:
        start = ann["start"]
        end = ann["end"]
        label = ann["label"]
        layer = ann["layer"]

        rich_text.stylize(
            f"bold {color_for(label)}",
            start,
            end,
        )

    console.print(rich_text)

    for ann in annotations:
        console.print(
            f"  [{color_for(ann['label'])}]"
            f"{ann['text']}[/] "
            f"→ {ann['label']} "
            f"({ann['layer']})"
        )

    console.print()


def render_corpus(data: dict) -> None:
    for index, document in enumerate(data.get("documents", []), start=1):
        console.rule(f"Document {index}")
        render_document(document)