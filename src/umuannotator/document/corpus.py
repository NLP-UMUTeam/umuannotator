from dataclasses import dataclass, field

from umuannotator.document.model import Document


@dataclass
class Corpus:
    documents: list[Document] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.documents)

    def append(self, document: Document) -> None:
        self.documents.append(document)