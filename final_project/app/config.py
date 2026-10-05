import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    google_api_key: str = field(default="", repr=False)
    google_embedding_model: str = "gemini-embedding-001"
    google_generation_model: str = "gemini-2.0-flash"
    chroma_path: Path = Path("./chroma")
    chunk_size: int = 300
    chunk_overlap: int = 60
    top_k: int = 4
    min_score: float = 0.35

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        settings = cls(
            google_api_key=os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY", ""),
            google_embedding_model=os.getenv(
                "GOOGLE_EMBEDDING_MODEL", cls.google_embedding_model
            ),
            google_generation_model=os.getenv(
                "GOOGLE_GENERATION_MODEL", cls.google_generation_model
            ),
            chroma_path=Path(os.getenv("CHROMA_PATH", str(cls.chroma_path))),
            chunk_size=int(os.getenv("CHUNK_SIZE", str(cls.chunk_size))),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", str(cls.chunk_overlap))),
            top_k=int(os.getenv("TOP_K", str(cls.top_k))),
            min_score=float(os.getenv("MIN_SCORE", str(cls.min_score))),
        )
        if (
            settings.chunk_size <= 0
            or not 0 <= settings.chunk_overlap < settings.chunk_size
        ):
            raise ValueError("CHUNK_OVERLAP must satisfy 0 <= overlap < CHUNK_SIZE")
        return settings


def get_settings() -> Settings:
    return Settings.from_env()
