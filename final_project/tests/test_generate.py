from app.generate import GenerationClient
from app.schemas import Citation


class FakeModels:
    def __init__(self) -> None:
        self.prompt = ""

    def generate_content(self, *, model: str, contents: str) -> object:
        self.prompt = contents
        return type(
            "Response", (), {"text": "La respuesta sintetiza la evidencia [1]."}
        )()


class FakeGoogleClient:
    def __init__(self) -> None:
        self.models = FakeModels()


def test_generation_formats_numbered_spanish_evidence_without_concatenating_chunks() -> (
    None
):
    google_client = FakeGoogleClient()
    generator = GenerationClient(
        api_key="test-key",
        model="modelo-prueba",
        client=google_client,
    )
    citations = [
        Citation(
            id="chunk-1",
            source="manual.pdf",
            text="El riego debe ser uniforme.",
            score=0.91,
        ),
        Citation(
            id="chunk-2",
            source="agenda.pdf",
            text="La fertilización depende del suelo.",
            score=0.82,
        ),
    ]

    answer = generator.answer("¿Cómo se maneja el cultivo?", citations)

    assert answer == "La respuesta sintetiza la evidencia [1]."
    assert "[1]" in google_client.models.prompt
    assert "[2]" in google_client.models.prompt
    assert citations[0].text in google_client.models.prompt
    assert citations[1].text in google_client.models.prompt
    assert answer != "\n".join(citation.text for citation in citations)
