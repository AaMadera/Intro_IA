import hashlib
import math
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field, field_validator

from app.chunk import chunk_text
from app.config import Settings, get_settings
from app.corpus import EXPECTED_CORPUS_FILES, CorpusManifest
from app.embed import EmbeddingClient
from app.extract import DocumentExtractionError, extract_document
from app.generate import GenerationClient
from app.retry import RetryExhaustedError
from app.schemas import ChunkRecord, Citation
from app.store import VectorStore

SUPPORTED_SUFFIXES = {".pdf", ".md", ".markdown", ".txt"}
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS_DIR = PROJECT_ROOT / "pdfs_seed"
DEFAULT_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ABSTENTION_MESSAGE = "No tengo evidencia suficiente en los documentos indexados para responder esta pregunta."


def _page_for_chunk(
    text: str, pages: list[dict[str, object]], chunk: str
) -> int | None:
    normalized_chunk = " ".join(chunk.split())
    if not normalized_chunk:
        return None
    normalized_text = " ".join(text.split())
    chunk_start = normalized_text.find(normalized_chunk)
    if chunk_start < 0:
        return None
    offset = 0
    for page in pages:
        page_text = " ".join(str(page.get("text", "")).split())
        page_end = offset + len(page_text)
        if offset <= chunk_start < page_end:
            page_number = page.get("page")
            return int(page_number) if isinstance(page_number, int) else None
        offset = page_end + 2
    return None


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = Field(default=None, ge=2, le=10)
    min_score: float | None = Field(default=None, ge=0.10, le=0.90)
    source: str | None = None

    @field_validator("min_score")
    @classmethod
    def min_score_must_use_supported_step(cls, value: float | None) -> float | None:
        if value is not None:
            step_index = round((value - 0.10) / 0.05)
            if not math.isclose(value, 0.10 + step_index * 0.05, abs_tol=1e-9):
                raise ValueError("min_score debe avanzar en pasos de 0.05.")
        return value

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("La pregunta no puede estar vacía.")
        return question

    @field_validator("source")
    @classmethod
    def source_must_contain_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        source = value.strip()
        return source or None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    abstained: bool


def create_app(
    settings: Settings | None = None,
    embedding_client: Any | None = None,
    generation_client: Any | None = None,
    store: VectorStore | None = None,
    corpus_dir: Path | None = None,
    processed_dir: Path | None = None,
) -> FastAPI:
    configured = settings or get_settings()
    vector_store = store or VectorStore(configured.chroma_path)
    embedder = embedding_client
    if embedder is None and configured.google_api_key:
        embedder = EmbeddingClient(
            configured.google_api_key,
            configured.google_embedding_model,
            retry_attempts=configured.model_retry_attempts,
            retry_backoff_seconds=configured.model_retry_backoff_seconds,
            batch_size=configured.embedding_batch_size,
        )
    generator = generation_client
    if generator is None and configured.google_api_key:
        generator = GenerationClient(
            configured.google_api_key,
            configured.google_generation_model,
            retry_attempts=configured.model_retry_attempts,
            retry_backoff_seconds=configured.model_retry_backoff_seconds,
        )

    app = FastAPI(title="Habanero RAG API")
    app.state.settings = configured
    app.state.store = vector_store
    app.state.embedding_client = embedder
    app.state.generation_client = generator
    app.state.corpus_dir = corpus_dir or DEFAULT_CORPUS_DIR
    app.state.processed_dir = processed_dir or DEFAULT_PROCESSED_DIR
    app.state.manifest = CorpusManifest(
        app.state.processed_dir / "corpus_manifest.json"
    )
    app.state.ingestion_manifest = CorpusManifest(
        app.state.processed_dir / "ingestion_manifest.json"
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        try:
            vector_store.count()
        except Exception:
            return {"api": "ok", "chroma": "error"}
        return {"api": "ok", "chroma": "ok"}

    @app.get("/corpus/status")
    def corpus_status() -> dict[str, Any]:
        files = app.state.manifest.sync_status(app.state.corpus_dir, vector_store)
        counts = {
            status: 0
            for status in ("loaded", "partial", "pending", "failed", "missing")
        }
        for file in files:
            counts[file["status"]] += 1
        return {
            "files": files,
            "uploads": list(app.state.ingestion_manifest.read().values()),
            "expected": len(EXPECTED_CORPUS_FILES),
            "loaded": counts["loaded"],
            "counts": counts,
        }

    @app.post("/ingest")
    async def ingest(
        files: list[UploadFile] | None = File(default=None),
        action: str | None = Form(default=None),
        path: str | None = Form(default=None),
    ) -> dict[str, Any]:
        if app.state.embedding_client is None:
            raise HTTPException(
                status_code=503,
                detail="No se configuró una clave para el servicio de embeddings.",
            )

        sources: list[tuple[str, bytes, str]] = []
        if files:
            for upload in files:
                sources.append(
                    (upload.filename or "archivo", await upload.read(), "upload")
                )

        if action and action.lower() in {"corpus", "bundled", "index_corpus"}:
            corpus_root = app.state.corpus_dir.resolve()
            corpus_path = Path(path).resolve() if path else corpus_root
            try:
                corpus_path.relative_to(corpus_root)
            except ValueError as error:
                raise HTTPException(
                    status_code=400,
                    detail="La ruta del corpus debe estar dentro del directorio configurado.",
                ) from error
            if corpus_path.is_file():
                corpus_files = [corpus_path]
            elif corpus_path.is_dir():
                corpus_files = sorted(
                    item
                    for item in corpus_path.iterdir()
                    if item.is_file() and item.suffix.lower() in SUPPORTED_SUFFIXES
                )
            else:
                corpus_files = []
            for source in corpus_files:
                sources.append((source.name, source.read_bytes(), "corpus"))

        if not sources:
            raise HTTPException(
                status_code=400,
                detail="Debe enviar archivos o solicitar la indexación del corpus.",
            )

        if action and action.lower() in {"corpus", "bundled", "index_corpus"}:
            app.state.manifest.sync_status(app.state.corpus_dir, vector_store)

        document_count = 0
        chunk_count = 0
        errors: list[dict[str, str]] = []
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            for filename, content, source_kind in sources:
                suffix = Path(filename).suffix.lower()
                if suffix not in SUPPORTED_SUFFIXES:
                    errors.append(
                        {
                            "file": filename,
                            "message": "Tipo de archivo no soportado. Use PDF, Markdown o texto.",
                        }
                    )
                    continue
                source_path = temporary_path / Path(filename).name
                source_path.write_bytes(content)
                progress_manifest = (
                    app.state.manifest
                    if source_kind == "corpus"
                    else app.state.ingestion_manifest
                )
                source_hash = hashlib.sha256(content).hexdigest()
                previous = progress_manifest.get(filename, source_hash)
                total_chunks = int(previous.get("total_chunks", 0) or 0)
                if (
                    previous.get("status") == "loaded"
                    and total_chunks > 0
                    and previous.get("chunk_size") == configured.chunk_size
                    and previous.get("chunk_overlap") == configured.chunk_overlap
                    and vector_store.count_chunks_for_source(filename, source_hash)
                    >= total_chunks
                ):
                    document_count += 1
                    continue
                try:
                    document = extract_document(source_path, app.state.processed_dir)
                except Exception as error:
                    if isinstance(error, ValueError):
                        message = "El archivo está vacío o no contiene texto extraíble."
                    elif isinstance(error, DocumentExtractionError):
                        message = f"No se pudo extraer el PDF: {error}"
                    else:
                        message = f"No se pudo leer el archivo: {type(error).__name__}: {error}"
                    errors.append(
                        {
                            "file": filename,
                            "message": message,
                        }
                    )
                    progress_manifest.record_failure(
                        filename,
                        message,
                        source_hash,
                        source=source_kind,
                    )
                    continue

                try:
                    records: list[ChunkRecord] = []
                    indexed_chunks = 0
                    text_chunks = chunk_text(
                        document.text,
                        configured.chunk_size,
                        configured.chunk_overlap,
                    )
                    records = [
                        ChunkRecord(
                            source=document.source_name,
                            text=text,
                            source_hash=document.source_sha256,
                            chunk_index=index,
                            page=_page_for_chunk(document.text, document.pages, text),
                        )
                        for index, text in enumerate(text_chunks)
                    ]
                    pending_records = vector_store.missing_chunks(records)
                    document_count += 1
                    indexed_chunks = len(records) - len(pending_records)
                    progress_manifest.record_progress(
                        filename,
                        document.source_sha256,
                        status="partial" if pending_records else "loaded",
                        total_chunks=len(records),
                        indexed_chunks=indexed_chunks,
                        source=source_kind,
                        chunk_size=configured.chunk_size,
                        chunk_overlap=configured.chunk_overlap,
                    )
                    for start in range(
                        0, len(pending_records), configured.embedding_batch_size
                    ):
                        batch = pending_records[
                            start : start + configured.embedding_batch_size
                        ]
                        embeddings = app.state.embedding_client.embed(
                            [record.text for record in batch],
                            "RETRIEVAL_DOCUMENT",
                        )
                        added = vector_store.add_chunks(batch, embeddings)
                        indexed_chunks += added
                        chunk_count += added
                        progress_manifest.record_progress(
                            filename,
                            document.source_sha256,
                            status="partial",
                            total_chunks=len(records),
                            indexed_chunks=indexed_chunks,
                            source=source_kind,
                            chunk_size=configured.chunk_size,
                            chunk_overlap=configured.chunk_overlap,
                        )
                    progress_manifest.record_success(
                        filename,
                        document.source_sha256,
                        len(records),
                        source=source_kind,
                        chunk_size=configured.chunk_size,
                        chunk_overlap=configured.chunk_overlap,
                    )
                except Exception as error:
                    if isinstance(error, RetryExhaustedError):
                        message = (
                            "Se alcanzó la cuota del servicio de embeddings; espere unos "
                            "minutos y vuelva a intentar. "
                            f"{error}"
                        )
                    else:
                        message = (
                            "No se pudo indexar el archivo: "
                            f"{type(error).__name__}: {error}"
                        )
                    errors.append(
                        {
                            "file": filename,
                            "message": message,
                        }
                    )
                    progress_manifest = (
                        app.state.manifest
                        if source_kind == "corpus"
                        else app.state.ingestion_manifest
                    )
                    if isinstance(error, RetryExhaustedError):
                        progress_manifest.record_progress(
                            filename,
                            document.source_sha256,
                            status="partial",
                            total_chunks=len(records),
                            indexed_chunks=indexed_chunks,
                            error=message,
                            source=source_kind,
                            chunk_size=configured.chunk_size,
                            chunk_overlap=configured.chunk_overlap,
                        )
                    else:
                        progress_manifest.record_failure(
                            filename,
                            message,
                            document.source_sha256,
                            source=source_kind,
                        )

        return {
            "documents": document_count,
            "chunks": chunk_count,
            "errors": errors,
        }

    @app.post("/query", response_model=QueryResponse)
    def query(request: QueryRequest) -> QueryResponse:
        if app.state.embedding_client is None:
            raise HTTPException(
                status_code=503,
                detail="No se configuró una clave para el servicio de embeddings.",
            )

        try:
            question_embedding = app.state.embedding_client.embed(
                [request.question], "RETRIEVAL_QUERY"
            )[0]
            citations = app.state.store.query(
                question_embedding,
                request.top_k if request.top_k is not None else configured.top_k,
                request.source,
            )
        except RetryExhaustedError as error:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"{error} El servicio puede estar ocupado o haber alcanzado "
                    "un límite temporal; inténtelo de nuevo más tarde."
                ),
            ) from error
        except Exception as error:
            raise HTTPException(
                status_code=502,
                detail="No se pudo consultar el servicio de búsqueda.",
            ) from error

        if not citations or max(citation.score for citation in citations) < (
            request.min_score if request.min_score is not None else configured.min_score
        ):
            return QueryResponse(
                answer=ABSTENTION_MESSAGE,
                citations=citations,
                abstained=True,
            )

        if app.state.generation_client is None:
            raise HTTPException(
                status_code=503,
                detail="No se configuró una clave para el servicio de generación.",
            )

        try:
            answer = app.state.generation_client.answer(request.question, citations)
        except RetryExhaustedError as error:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"{error} El servicio puede estar ocupado o haber alcanzado "
                    "un límite temporal; inténtelo de nuevo más tarde."
                ),
            ) from error
        except Exception as error:
            raise HTTPException(
                status_code=502,
                detail="No se pudo generar una respuesta con la evidencia recuperada.",
            ) from error
        return QueryResponse(answer=answer, citations=citations, abstained=False)

    @app.delete("/documents/{source}")
    def delete_document(source: str) -> dict[str, Any]:
        deleted = vector_store.delete_source(source)
        for manifest in (app.state.manifest, app.state.ingestion_manifest):
            entries = manifest.read()
            updated = []
            for entry in entries.values():
                if entry.get("file") == source:
                    entry = {
                        **entry,
                        "status": "pending",
                        "chunks": 0,
                        "indexed_chunks": 0,
                        "error": "Documento borrado del índice; puede reindexarse.",
                    }
                updated.append(entry)
            if len(updated) != len(entries) or any(
                entry.get("file") == source for entry in entries.values()
            ):
                manifest.write(updated)
        return {"source": source, "deleted_chunks": deleted}

    @app.post("/documents/{source}/reindex")
    async def reindex_document(source: str) -> dict[str, Any]:
        source_path = app.state.corpus_dir / source
        if source_path.is_file() and source_path.suffix.lower() in SUPPORTED_SUFFIXES:
            vector_store.delete_source(source)
            return await ingest(files=None, action="corpus", path=str(source_path))

        entry = app.state.ingestion_manifest.find(source, "upload")
        source_hash = str(entry.get("sha256", ""))
        cached_path = app.state.processed_dir / f"{source_hash[:12]}.txt"
        if not source_hash or not cached_path.is_file():
            raise HTTPException(
                status_code=404,
                detail="No se encontró el documento ni su extracción cacheada.",
            )

        vector_store.delete_source(source)
        text = cached_path.read_text(encoding="utf-8")
        records = [
            ChunkRecord(
                source=source,
                text=chunk,
                source_hash=source_hash,
                chunk_index=index,
            )
            for index, chunk in enumerate(
                chunk_text(text, configured.chunk_size, configured.chunk_overlap)
            )
        ]
        added = 0
        try:
            for start in range(0, len(records), configured.embedding_batch_size):
                batch = records[start : start + configured.embedding_batch_size]
                embeddings = app.state.embedding_client.embed(
                    [record.text for record in batch], "RETRIEVAL_DOCUMENT"
                )
                added += vector_store.add_chunks(batch, embeddings)
            app.state.ingestion_manifest.record_success(
                source,
                source_hash,
                len(records),
                source="upload",
                chunk_size=configured.chunk_size,
                chunk_overlap=configured.chunk_overlap,
            )
        except Exception as error:
            message = (
                f"No se pudo reindexar el archivo: {type(error).__name__}: {error}"
            )
            app.state.ingestion_manifest.record_progress(
                source,
                source_hash,
                status="partial",
                total_chunks=len(records),
                indexed_chunks=added,
                error=message,
                source="upload",
                chunk_size=configured.chunk_size,
                chunk_overlap=configured.chunk_overlap,
            )
            return {
                "documents": 0,
                "chunks": added,
                "errors": [{"file": source, "message": message}],
            }
        return {"documents": 1, "chunks": added, "errors": []}

    return app


app = create_app()
