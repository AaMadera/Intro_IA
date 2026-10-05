from types import SimpleNamespace

from app.embed import EmbeddingClient


class FakeModels:
    def __init__(self) -> None:
        self.batch_sizes: list[int] = []

    def embed_content(
        self, *, model: str, contents: list[str], config: object
    ) -> object:
        self.batch_sizes.append(len(contents))
        return SimpleNamespace(
            embeddings=[
                SimpleNamespace(values=[float(index)])
                for index, _ in enumerate(contents)
            ]
        )


def test_embeddings_are_sent_in_configured_batches() -> None:
    models = FakeModels()
    client = EmbeddingClient(
        api_key="test-key",
        model="test-model",
        client=SimpleNamespace(models=models),
        batch_size=2,
    )

    embeddings = client.embed(["uno", "dos", "tres", "cuatro", "cinco"], "DOCUMENT")

    assert models.batch_sizes == [2, 2, 1]
    assert len(embeddings) == 5
