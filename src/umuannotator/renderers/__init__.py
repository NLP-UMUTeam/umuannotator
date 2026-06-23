DEFAULT_COLOR = "#eeeeee"

LAYER_COLORS = {
    "ontology": "#ffd6d6",
    "ner": "#d6ffd6",
    "temporal": "#d6e4ff",
    "entity-linking": "#fff4bf",
    "pizza-order": "#ffe0b2",
    "regex": "#e6d6ff",
}


def layer_color(layer: str | None) -> str:
    if not layer:
        return DEFAULT_COLOR

    return LAYER_COLORS.get(layer, DEFAULT_COLOR)


def collect_layers(data: dict) -> list[str]:
    layers = set()

    for document in data.get("documents", []):
        for annotation in document.get("annotations", []):
            layer = annotation.get("layer")
            if layer:
                layers.add(layer)

    return sorted(layers)