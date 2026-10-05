import hashlib
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedDocument:
    source_name: str
    processed_path: Path
    text: str
    pages: list[dict[str, object]] = field(default_factory=list)
    source_sha256: str = ""


def _extract_with_opendataloader(path: Path) -> tuple[str, list[dict[str, object]]]:
    result = subprocess.run(
        ["opendataloader-pdf", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("opendataloader-pdf did not return extracted text")
    return result.stdout.strip(), []


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
        except Exception:
            return _extract_with_pypdf(path)
    if path.suffix.lower() in {".md", ".markdown", ".txt"}:
        return path.read_text(encoding="utf-8"), []
    raise ValueError(f"Unsupported document type: {path.suffix}")


def extract_document(path: Path, processed_dir: Path) -> ExtractedDocument:
    source_bytes = path.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    text, pages = _read_source(path)
    text = text.strip()
    if not text:
        raise ValueError(f"Empty extraction for {path.name}")

    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_path = processed_dir / f"{path.stem}-{source_sha256[:12]}.txt"
    processed_path.write_text(text, encoding="utf-8")
    return ExtractedDocument(
        source_name=path.name,
        processed_path=processed_path,
        text=text,
        pages=pages,
        source_sha256=source_sha256,
    )
