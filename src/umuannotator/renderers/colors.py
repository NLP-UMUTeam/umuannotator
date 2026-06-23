DEFAULT_COLOR = "#eeeeee"

LAYER_COLORS = {
    "ontology": "#ffd6d6",
    "ner": "#d6ffd6",
    "temporal": "#d6e4ff",
    "entity-linking": "#fff4bf",
    "pizza-order": "#ffe0b2",
    "regex": "#e6d6ff",
}


def layer_color(layer: str | None, custom_colors: dict | None = None) -> str:
    if not layer:
        return DEFAULT_COLOR

    if custom_colors and layer in custom_colors:
        return custom_colors[layer]

    return LAYER_COLORS.get(layer, DEFAULT_COLOR)


def collect_layers(data: dict) -> list[str]:
    layers = set()

    for document in data.get("documents", []):
        for annotation in document.get("annotations", []):
            layer = annotation.get("layer")
            if layer:
                layers.add(layer)

    return sorted(layers)


def collect_layer_colors(config: dict) -> dict[str, str]:
    colors = {}

    for item in config.get("annotators", []):
        if not isinstance(item, dict):
            continue

        color = item.get("color")
        if not color:
            continue

        layer = item.get("layer") or _default_layer_for(item.get("name"))
        if layer:
            colors[layer] = color

    return colors


def _default_layer_for(name: str | None) -> str | None:
    return {
        "ontology": "ontology",
        "stanza-ner": "ner",
        "temporal": "temporal",
        "dbpedia": "entity-linking",
        "regex": "regex",
    }.get(name)