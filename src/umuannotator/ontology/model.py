from dataclasses import dataclass, field


@dataclass
class Concept:
    uri: str
    name: str
    labels: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    parents: list[str] = field(default_factory=list)