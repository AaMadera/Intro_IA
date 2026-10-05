from typing import Any

from google import genai
from google.genai import types

from app.retry import call_with_retries


class EmbeddingClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        client: Any | None = None,
        retry_attempts: int = 5,
        retry_backoff_seconds: float = 5.0,
        batch_size: int = 32,
    ) -> None:
        self.model = model
        self.client = client or genai.Client(api_key=api_key)
        self.retry_attempts = retry_attempts
        self.retry_backoff_seconds = retry_backoff_seconds
        if batch_size < 1:
            raise ValueError("batch_size must be at least one")
        self.batch_size = batch_size

    def embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            response = call_with_retries(
                f"El servicio de embeddings (lote {start + 1}-{start + len(batch)})",
                lambda batch=batch: self.client.models.embed_content(
                    model=self.model,
                    contents=batch,
                    config=types.EmbedContentConfig(task_type=task_type),
                ),
                attempts=self.retry_attempts,
                backoff_seconds=self.retry_backoff_seconds,
            )
            embeddings.extend(
                list(embedding.values) for embedding in response.embeddings
            )
        return embeddings
