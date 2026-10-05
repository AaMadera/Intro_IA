from typing import Any

from google import genai

from app.schemas import Citation
from app.retry import call_with_retries


class GenerationClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        client: Any | None = None,
        retry_attempts: int = 3,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        self.model = model
        self.client = client or genai.Client(api_key=api_key)
        self.retry_attempts = retry_attempts
        self.retry_backoff_seconds = retry_backoff_seconds

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
        response = call_with_retries(
            "El modelo de generación",
            lambda: self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            ),
            attempts=self.retry_attempts,
            backoff_seconds=self.retry_backoff_seconds,
        )
        answer = getattr(response, "text", None)
        if not answer:
            raise RuntimeError("Google AI no devolvió una respuesta")
        return answer.strip()
