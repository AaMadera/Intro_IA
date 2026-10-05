import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


EXPECTED_CORPUS_FILES: tuple[str, ...] = (
    "2025_Manual-fertilizacion_GRC.pdf",
    "Agenda_Tecnica_Yucatan_2017.pdf",
    "Ficha-Tecnica-Chile-Hab_Balche.pdf",
    "Ficha-Tecnica-Chile-Hab_Kisin.pdf",
)


class CorpusManifest:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> dict[str, dict[str, Any]]:
        if not self.path.is_file():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def write(self, entries: list[dict[str, Any]]) -> None:
        payload = {str(entry["file"]): entry for entry in entries}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(self.path)

    def sync_status(self, corpus_dir: Path, store: Any | None) -> list[dict[str, Any]]:
        existing = self.read()
        entries: list[dict[str, Any]] = []
        for filename in EXPECTED_CORPUS_FILES:
            path = corpus_dir / filename
            previous = existing.get(filename, {})
            if not path.is_file():
                entries.append(
                    {
                        "file": filename,
                        "source": "bundled",
                        "sha256": previous.get("sha256"),
                        "status": "missing",
                        "chunks": 0,
                        "total_chunks": int(previous.get("total_chunks", 0) or 0),
                        "indexed_chunks": 0,
                        "processed_at": previous.get("processed_at"),
                        "error": "El archivo no se encuentra en el corpus inicial.",
                    }
                )
                continue

            source_hash = self.source_hash(path)
            status = previous.get("status")
            if previous.get("sha256") != source_hash:
                status = "pending"
            elif status not in {"loaded", "partial", "failed"}:
                status = "pending"
            chunks = int(previous.get("chunks", 0) or 0)
            if store is not None and status in {"loaded", "partial"}:
                chunks = store.count_chunks_for_source(filename, source_hash)
            entries.append(
                {
                    "file": filename,
                    "source": "bundled",
                    "sha256": source_hash,
                    "status": status,
                    "chunks": chunks,
                    "total_chunks": int(previous.get("total_chunks", chunks) or 0),
                    "indexed_chunks": chunks,
                    "processed_at": previous.get("processed_at"),
                    "error": previous.get("error")
                    if status in {"failed", "partial"}
                    else None,
                }
            )
        self.write(entries)
        return entries

    def record_success(
        self,
        filename: str,
        source_hash: str,
        chunks: int,
        source: str = "bundled",
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self.record_progress(
            filename,
            source_hash,
            status="loaded",
            total_chunks=chunks,
            indexed_chunks=chunks,
            error=None,
            source=source,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def record_progress(
        self,
        filename: str,
        source_hash: str,
        *,
        status: str,
        total_chunks: int,
        indexed_chunks: int,
        error: str | None = None,
        source: str = "bundled",
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        entries = self.read()
        previous = self.get(filename, source_hash) or entries.get(filename, {})
        key = filename if source == "bundled" else f"{filename}:{source_hash}"
        entry = {
            "file": filename,
            "source": source,
            "sha256": source_hash,
            "status": status,
            "chunks": indexed_chunks,
            "total_chunks": total_chunks,
            "indexed_chunks": indexed_chunks,
            "processed_at": datetime.now(UTC).isoformat(),
            "error": error,
        }
        if chunk_size is not None:
            entry["chunk_size"] = chunk_size
        if chunk_overlap is not None:
            entry["chunk_overlap"] = chunk_overlap
        entries[key] = entry
        self.write(list(entries.values()))

    def get(self, filename: str, source_hash: str) -> dict[str, Any]:
        return next(
            (
                entry
                for entry in self.read().values()
                if entry.get("file") == filename and entry.get("sha256") == source_hash
            ),
            {},
        )

    def find(self, filename: str, source: str) -> dict[str, Any]:
        entries = [
            entry
            for entry in self.read().values()
            if entry.get("file") == filename and entry.get("source") == source
        ]
        return entries[-1] if entries else {}

    def record_failure(
        self,
        filename: str,
        message: str,
        source_hash: str | None = None,
        source: str = "bundled",
    ) -> None:
        entries = self.read()
        previous = self.get(filename, source_hash) or entries.get(filename, {})
        key = filename if source == "bundled" else f"{filename}:{source_hash}"
        entries[key] = {
            "file": filename,
            "source": source,
            "sha256": source_hash or previous.get("sha256"),
            "status": "failed",
            "chunks": int(previous.get("chunks", 0) or 0),
            "total_chunks": int(previous.get("total_chunks", 0) or 0),
            "indexed_chunks": int(previous.get("indexed_chunks", 0) or 0),
            "processed_at": datetime.now(UTC).isoformat(),
            "error": message,
        }
        self.write(list(entries.values()))

    @staticmethod
    def source_hash(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
