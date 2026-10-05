from typing import Any

from google import genai
from google.genai import types


class EmbeddingClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.client = client or genai.Client(api_key=api_key)

    def embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        return [list(embedding.values) for embedding in response.embeddings]
