import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
import tempfile

from pypdf import PdfReader


class DocumentExtractionError(RuntimeError):
    """Raised when all configured PDF extractors fail."""


@dataclass(frozen=True)
class ExtractedDocument:
    source_name: str
    processed_path: Path
    text: str
    pages: list[dict[str, object]] = field(default_factory=list)
    source_sha256: str = ""


def _extract_with_opendataloader(path: Path) -> tuple[str, list[dict[str, object]]]:
    import opendataloader_pdf

    with tempfile.TemporaryDirectory() as output_directory:
        opendataloader_pdf.convert(
            input_path=[str(path)],
            output_dir=output_directory,
            format="markdown",
        )
        markdown_files = sorted(Path(output_directory).rglob("*.md"))
        if not markdown_files:
            raise RuntimeError("OpenDataLoader no devolvió Markdown")
        text = "\n\n".join(
            file.read_text(encoding="utf-8") for file in markdown_files
        ).strip()
        if not text:
            raise RuntimeError("OpenDataLoader devolvió texto vacío")
        return text, []


def _extract_with_pypdf(path: Path) -> tuple[str, list[dict[str, object]]]:
    reader = PdfReader(str(path))
    page_text: list[str] = []
    pages: list[dict[str, object]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            page_text.append(text)
        pages.append({"page": page_number, "text": text})
    return "\n\n".join(page_text), pages


def _read_source(path: Path) -> tuple[str, list[dict[str, object]]]:
    if path.suffix.lower() == ".pdf":
        try:
            return _extract_with_opendataloader(path)
        except Exception as opendataloader_error:
            try:
                return _extract_with_pypdf(path)
            except Exception as pypdf_error:
                raise DocumentExtractionError(
                    "OpenDataLoader: "
                    f"{type(opendataloader_error).__name__}: {opendataloader_error}; "
                    "pypdf: "
                    f"{type(pypdf_error).__name__}: {pypdf_error}"
                ) from pypdf_error
    if path.suffix.lower() in {".md", ".markdown", ".txt"}:
        return path.read_text(encoding="utf-8"), []
    raise ValueError(f"Unsupported document type: {path.suffix}")


def extract_document(path: Path, processed_dir: Path) -> ExtractedDocument:
    source_bytes = path.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_path = processed_dir / f"{source_sha256[:12]}.txt"
    metadata_path = processed_path.with_suffix(".json")
    if processed_path.is_file() and metadata_path.is_file():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("source_sha256") == source_sha256:
                return ExtractedDocument(
                    source_name=path.name,
                    processed_path=processed_path,
                    text=processed_path.read_text(encoding="utf-8"),
                    pages=list(metadata.get("pages", [])),
                    source_sha256=source_sha256,
                )
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    text, pages = _read_source(path)
    text = text.strip()
    if not text:
        raise ValueError(f"Empty extraction for {path.name}")
    processed_path.write_text(text, encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {"source_name": path.name, "source_sha256": source_sha256, "pages": pages},
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    return ExtractedDocument(
        source_name=path.name,
        processed_path=processed_path,
        text=text,
        pages=pages,
        source_sha256=source_sha256,
    )
