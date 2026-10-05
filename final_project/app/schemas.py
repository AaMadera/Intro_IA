from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkRecord:
    source: str
    text: str
    source_hash: str
    chunk_index: int
    page: int | None = None
    title: str | None = None
    id: str | None = None

    @property
    def stable_id(self) -> str:
        return self.id or f"{self.source_hash}:{self.chunk_index}"


@dataclass(frozen=True)
class Citation:
    id: str
    source: str
    text: str
    score: float
    page: int | None = None
    chunk_index: int | None = None
    title: str | None = None
