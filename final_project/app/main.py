import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field, field_validator

from app.chunk import chunk_text
from app.config import Settings, get_settings
from app.embed import EmbeddingClient
from app.extract import extract_document
from app.generate import GenerationClient
from app.store import VectorStore
from app.schemas import ChunkRecord, Citation


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
    chunk_start = text.find(chunk)
    if chunk_start < 0:
        return None
    offset = 0
    for page in pages:
        page_text = str(page.get("text", ""))
        page_end = offset + len(page_text)
        if offset <= chunk_start < page_end:
            page_number = page.get("page")
            return int(page_number) if isinstance(page_number, int) else None
        offset = page_end + 2
    return None


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = Field(default=None, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("La pregunta no puede estar vacía.")
        return question


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
            configured.google_api_key, configured.google_embedding_model
        )
    generator = generation_client
    if generator is None and configured.google_api_key:
        generator = GenerationClient(
            configured.google_api_key, configured.google_generation_model
        )

    app = FastAPI(title="Habanero RAG API")
    app.state.settings = configured
    app.state.store = vector_store
    app.state.embedding_client = embedder
    app.state.generation_client = generator
    app.state.corpus_dir = corpus_dir or DEFAULT_CORPUS_DIR
    app.state.processed_dir = processed_dir or DEFAULT_PROCESSED_DIR

    @app.get("/health")
    def health() -> dict[str, str]:
        try:
            vector_store.count()
        except Exception:
            return {"api": "ok", "chroma": "error"}
        return {"api": "ok", "chroma": "ok"}

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
                try:
                    document = extract_document(source_path, app.state.processed_dir)
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
                    embeddings = app.state.embedding_client.embed(
                        [record.text for record in records], "RETRIEVAL_DOCUMENT"
                    )
                    added = vector_store.add_chunks(records, embeddings)
                    document_count += 1
                    chunk_count += added
                except Exception as error:
                    message = (
                        "El archivo está vacío o no contiene texto extraíble."
                        if isinstance(error, ValueError)
                        else "No se pudo procesar el archivo."
                    )
                    errors.append(
                        {
                            "file": filename,
                            "message": message,
                        }
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
                question_embedding, request.top_k or configured.top_k
            )
        except Exception as error:
            raise HTTPException(
                status_code=502,
                detail="No se pudo consultar el servicio de búsqueda.",
            ) from error

        if (
            not citations
            or max(citation.score for citation in citations) < configured.min_score
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
        except Exception as error:
            raise HTTPException(
                status_code=502,
                detail="No se pudo generar una respuesta con la evidencia recuperada.",
            ) from error
        return QueryResponse(answer=answer, citations=citations, abstained=False)

    return app


app = create_app()
