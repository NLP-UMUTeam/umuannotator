from dataclasses import dataclass, field


@dataclass
class OntologyConfig:
    path: str | None = None
    language: str = "es"


@dataclass
class ResolverConfig:
    enabled: bool = True
    strategy: str = "longest_match"


@dataclass
class ExtendedTfidfConfig:
    enabled: bool = False
    layer: str = "ontology"
    max_distance: int = 5
    direction: str = "ancestors"
    decay_type: str = "exponential"
    decay_value: float = 0.5


@dataclass
class MetricsConfig:
    tfidf_enabled: bool = False
    extended_tfidf: ExtendedTfidfConfig = field(
        default_factory=ExtendedTfidfConfig
    )