from typing import Any

from google import genai

from app.schemas import Citation


class GenerationClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.client = client or genai.Client(api_key=api_key)

    def answer(self, question: str, citations: list[Citation]) -> str:
        evidence = "\n\n".join(
            f"[{index}] Fuente: {citation.source}\n{citation.text}"
            for index, citation in enumerate(citations, start=1)
        )
        prompt = (
            "Responde en español mexicano usando únicamente la evidencia proporcionada. "
            "No uses conocimiento externo. Si la evidencia no es suficiente, dilo "
            "claramente. Cita las fuentes con el número entre corchetes, por ejemplo [1].\n\n"
            f"Pregunta: {question}\n\nEvidencia:\n{evidence}"
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        answer = getattr(response, "text", None)
        if not answer:
            raise RuntimeError("Google AI no devolvió una respuesta")
        return answer.strip()
