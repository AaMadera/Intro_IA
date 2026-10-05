import os
from collections.abc import Iterable, Mapping
from typing import Any

import httpx
import streamlit as st


DEFAULT_API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 30.0


class UIClientError(RuntimeError):
    """Error safe to show in the Streamlit interface."""


def get_api_base_url() -> str:
    return os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")


def _error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return "La API devolvió un error sin detalles."
    if isinstance(payload, Mapping) and isinstance(payload.get("detail"), str):
        return str(payload["detail"])
    return "La API devolvió una respuesta de error inesperada."


def _post_json(path: str, **kwargs: Any) -> dict[str, Any]:
    url = f"{get_api_base_url()}{path}"
    try:
        response = httpx.post(url, timeout=REQUEST_TIMEOUT, **kwargs)
        if response.is_error:
            raise UIClientError(_error_detail(response))
        payload = response.json()
    except UIClientError:
        raise
    except httpx.RequestError as error:
        raise UIClientError(
            "API no disponible. Verifique que el servicio FastAPI esté activo."
        ) from error
    except (TypeError, ValueError) as error:
        raise UIClientError("La API devolvió una respuesta inválida.") from error

    if not isinstance(payload, dict):
        raise UIClientError("La API devolvió una respuesta inválida.")
    return payload


def _require_keys(payload: dict[str, Any], keys: Iterable[str]) -> dict[str, Any]:
    if any(key not in payload for key in keys):
        raise UIClientError("La API devolvió una respuesta inválida.")
    return payload


def index_corpus() -> dict[str, Any]:
    payload = _post_json("/ingest", data={"action": "corpus"})
    return _require_keys(payload, ("documents", "chunks", "errors"))


def upload_documents(uploaded_files: Iterable[Any]) -> dict[str, Any]:
    files = [
        (
            "files",
            (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type or "application/octet-stream",
            ),
        )
        for uploaded_file in uploaded_files
    ]
    if not files:
        raise UIClientError("Seleccione al menos un archivo para cargar.")
    payload = _post_json("/ingest", files=files)
    return _require_keys(payload, ("documents", "chunks", "errors"))


def ask_question(question: str, top_k: int | None = None) -> dict[str, Any]:
    if not question.strip():
        raise UIClientError("La pregunta no puede estar vacía.")
    request: dict[str, Any] = {"question": question}
    if top_k is not None:
        request["top_k"] = top_k
    payload = _post_json("/query", json=request)
    return _require_keys(payload, ("answer", "citations", "abstained"))


def _show_ingestion_result(result: Mapping[str, Any]) -> None:
    st.success(
        f"Documentos procesados: {result['documents']}. "
        f"Fragmentos indexados: {result['chunks']}."
    )
    errors = result.get("errors", [])
    if errors:
        for error in errors:
            st.warning(
                f"{error.get('file', 'Archivo')}: {error.get('message', 'Error desconocido.')}"
            )


def _show_answer(result: Mapping[str, Any]) -> None:
    st.subheader("Respuesta")
    st.write(result["answer"])
    citations = result["citations"]
    if result["abstained"]:
        st.info("No se encontró evidencia suficiente en el corpus indexado.")
    elif citations:
        st.subheader("Fuentes")
        for index, citation in enumerate(citations, start=1):
            source = citation.get("source", "Fuente desconocida")
            score = citation.get("score", "n/d")
            page = citation.get("page")
            page_label = f" | página {page}" if page is not None else ""
            with st.expander(f"[{index}] {source} | puntuación: {score}{page_label}"):
                st.write(citation.get("text", "Sin texto de fragmento."))


def main() -> None:
    st.set_page_config(page_title="Habanero RAG", page_icon="🌶️")
    st.title("Consulta documental sobre chile habanero")
    st.caption(f"API: {get_api_base_url()}")

    st.header("Corpus inicial")
    if st.button("Indexar corpus inicial"):
        with st.spinner("Indexando el corpus inicial..."):
            try:
                _show_ingestion_result(index_corpus())
            except UIClientError as error:
                st.error(str(error))

    st.header("Agregar documentos")
    uploaded_files = st.file_uploader(
        "Cargar PDF, Markdown o texto",
        type=["pdf", "md", "markdown", "txt"],
        accept_multiple_files=True,
    )
    if st.button("Cargar documentos"):
        with st.spinner("Procesando documentos..."):
            try:
                _show_ingestion_result(upload_documents(uploaded_files or []))
            except UIClientError as error:
                st.error(str(error))

    st.header("Hacer una pregunta")
    question = st.text_input("Pregunta en español")
    if st.button("Consultar"):
        with st.spinner("Buscando evidencia y preparando la respuesta..."):
            try:
                _show_answer(ask_question(question))
            except UIClientError as error:
                st.error(str(error))


if __name__ == "__main__":
    main()
