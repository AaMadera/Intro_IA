import os
from collections.abc import Iterable, Mapping
from typing import Any

import httpx
import streamlit as st


DEFAULT_API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 30.0
INGEST_TIMEOUT = 300.0


def _query_timeout_from_env() -> float:
    try:
        timeout = float(os.getenv("QUERY_TIMEOUT_SECONDS", "60"))
    except ValueError:
        return 60.0
    return timeout if timeout > 0 else 60.0


QUERY_TIMEOUT = _query_timeout_from_env()


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


def _post_json(
    path: str, *, timeout: float = REQUEST_TIMEOUT, **kwargs: Any
) -> dict[str, Any]:
    url = f"{get_api_base_url()}{path}"
    try:
        response = httpx.post(url, timeout=timeout, **kwargs)
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


def _get_json(path: str, *, timeout: float = REQUEST_TIMEOUT) -> dict[str, Any]:
    url = f"{get_api_base_url()}{path}"
    try:
        response = httpx.get(url, timeout=timeout)
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


def _delete_json(path: str) -> dict[str, Any]:
    url = f"{get_api_base_url()}{path}"
    try:
        response = httpx.delete(url, timeout=REQUEST_TIMEOUT)
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
    payload = _post_json("/ingest", timeout=INGEST_TIMEOUT, data={"action": "corpus"})
    return _require_keys(payload, ("documents", "chunks", "errors"))


def get_corpus_status() -> dict[str, Any]:
    payload = _get_json("/corpus/status")
    return _require_keys(payload, ("files", "expected", "loaded", "counts"))


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
    payload = _post_json("/ingest", timeout=INGEST_TIMEOUT, files=files)
    return _require_keys(payload, ("documents", "chunks", "errors"))


def ask_question(
    question: str,
    top_k: int | None = None,
    min_score: float | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    if not question.strip():
        raise UIClientError("La pregunta no puede estar vacía.")
    request: dict[str, Any] = {"question": question}
    if top_k is not None:
        request["top_k"] = top_k
    if min_score is not None:
        request["min_score"] = min_score
    if source is not None:
        request["source"] = source
    payload = _post_json("/query", timeout=QUERY_TIMEOUT, json=request)
    return _require_keys(payload, ("answer", "citations", "abstained"))


def delete_document(source: str) -> dict[str, Any]:
    payload = _delete_json(f"/documents/{httpx.URL(source).raw_path.decode()}")
    return _require_keys(payload, ("source", "deleted_chunks"))


def reindex_document(source: str) -> dict[str, Any]:
    payload = _post_json(
        f"/documents/{httpx.URL(source).raw_path.decode()}/reindex",
        timeout=INGEST_TIMEOUT,
    )
    return _require_keys(payload, ("documents", "chunks", "errors"))


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


def _show_answer(result: Mapping[str, Any], *, allow_expanders: bool = True) -> None:
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
            citation_label = f"[{index}] {source} | puntuación: {score}{page_label}"
            if allow_expanders:
                with st.expander(citation_label):
                    st.write(citation.get("text", "Sin texto de fragmento."))
            else:
                st.markdown(f"**{citation_label}**")
                st.write(citation.get("text", "Sin texto de fragmento."))


def _show_corpus_status(status: Mapping[str, Any]) -> None:
    st.subheader(f"{status['loaded']}/{status['expected']} PDFs cargados")
    for file in status["files"]:
        indexed = file.get("indexed_chunks", file["chunks"])
        total = file.get("total_chunks", 0)
        progress = (
            f" | {indexed}/{total} fragmentos" if total else f" | {indexed} fragmentos"
        )
        label = f"{file['file']}{progress}"
        if file["status"] == "loaded":
            st.success(f"{label} | cargado")
        elif file["status"] == "partial":
            st.warning(
                f"{label} | parcial. {file.get('error', 'Espere unos minutos y vuelva a intentar.')}"
            )
        elif file["status"] == "failed":
            st.error(
                f"{label} | no se pudo cargar: {file.get('error', 'Error desconocido.')}"
            )
        elif file["status"] == "missing":
            st.warning(
                f"{label} | archivo faltante: {file.get('error', 'No encontrado.')}"
            )
        else:
            st.info(f"{label} | pendiente de indexar")
    uploads = status.get("uploads", [])
    if uploads:
        st.subheader("Documentos cargados")
        for file in uploads:
            indexed = file.get("indexed_chunks", file.get("chunks", 0))
            total = file.get("total_chunks", 0)
            label = f"{file['file']} | {indexed}/{total} fragmentos"
            if file.get("status") == "loaded":
                st.success(f"{label} | cargado")
            elif file.get("status") == "partial":
                st.warning(
                    f"{label} | parcial. {file.get('error', 'Espere unos minutos y vuelva a intentar.')}"
                )
            else:
                st.error(f"{label} | {file.get('error', 'No se pudo indexar.')}")


def _show_history(history: list[Mapping[str, Any]]) -> None:
    if not history:
        st.info("Todavia no hay preguntas consultadas en esta sesion.")
        return
    for item in reversed(history):
        with st.expander(item["question"]):
            _show_answer(item["result"], allow_expanders=False)


def main() -> None:
    st.set_page_config(page_title="Habanero RAG", page_icon="🌶️")
    st.title("Consulta documental sobre chile habanero")
    st.caption(f"API: {get_api_base_url()}")

    if "top_k" not in st.session_state:
        st.session_state.top_k = 4
    if "min_score" not in st.session_state:
        st.session_state.min_score = 0.35
    if "history" not in st.session_state:
        st.session_state.history = []

    consulta, historial, corpus, configuracion = st.tabs(
        ["Consulta", "Historial", "Corpus", "Configuracion"]
    )
    with consulta:
        st.header("Hacer una pregunta")
        question = st.text_input("Pregunta en español")
        source_options = ["Todas"]
        try:
            status = get_corpus_status()
            source_options.extend(
                sorted(
                    {
                        item["file"]
                        for item in status["files"] + status.get("uploads", [])
                    }
                )
            )
        except UIClientError:
            pass
        selected_source = st.selectbox("Fuente", source_options)
        if st.button("Consultar"):
            with st.spinner("Buscando evidencia y preparando la respuesta..."):
                try:
                    result = ask_question(
                        question,
                        top_k=st.session_state.top_k,
                        min_score=st.session_state.min_score,
                        source=None if selected_source == "Todas" else selected_source,
                    )
                    st.session_state.history.append(
                        {"question": question, "result": result}
                    )
                    _show_answer(result)
                except UIClientError as error:
                    st.error(str(error))

    with historial:
        st.header("Historial de preguntas")
        _show_history(st.session_state.history)

    with corpus:
        st.header("Corpus inicial")
        corpus_status: dict[str, Any] | None = None
        try:
            corpus_status = get_corpus_status()
            _show_corpus_status(corpus_status)
        except UIClientError as error:
            st.error(str(error))
        if st.button("Indexar corpus inicial"):
            with st.spinner("Indexando el corpus inicial..."):
                try:
                    _show_ingestion_result(index_corpus())
                    _show_corpus_status(get_corpus_status())
                except UIClientError as error:
                    st.error(str(error))

        managed_sources = []
        if corpus_status:
            managed_sources = sorted(
                {
                    item["file"]
                    for item in corpus_status["files"]
                    + corpus_status.get("uploads", [])
                }
            )
        if managed_sources:
            selected_document = st.selectbox("Documento", managed_sources)
            col_delete, col_reindex = st.columns(2)
            with col_delete:
                if st.button("Borrar documento"):
                    try:
                        st.success(delete_document(selected_document))
                    except UIClientError as error:
                        st.error(str(error))
            with col_reindex:
                if st.button("Reindexar documento"):
                    try:
                        _show_ingestion_result(reindex_document(selected_document))
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

    with configuracion:
        st.header("Configuracion de consulta")
        st.selectbox("top_k", options=list(range(2, 11)), key="top_k")
        st.slider(
            "min_score",
            min_value=0.10,
            max_value=0.90,
            step=0.05,
            key="min_score",
        )


if __name__ == "__main__":
    main()
