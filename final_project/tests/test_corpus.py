import json
from pathlib import Path

from app.corpus import CorpusManifest, EXPECTED_CORPUS_FILES


def make_corpus(tmp_path: Path) -> Path:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    for filename in EXPECTED_CORPUS_FILES:
        (corpus / filename).write_text(f"Contenido de {filename}", encoding="utf-8")
    return corpus


def test_manifest_reports_pending_and_missing_seed_pdfs(tmp_path: Path) -> None:
    corpus = make_corpus(tmp_path)
    (corpus / EXPECTED_CORPUS_FILES[-1]).unlink()

    entries = CorpusManifest(
        tmp_path / "processed" / "corpus_manifest.json"
    ).sync_status(corpus, store=None)

    assert len(entries) == 4
    assert entries[-1]["status"] == "missing"
    assert all(entry["status"] == "pending" for entry in entries[:-1])


def test_manifest_persists_success_and_detects_changed_source(tmp_path: Path) -> None:
    corpus = make_corpus(tmp_path)
    manifest = CorpusManifest(tmp_path / "processed" / "corpus_manifest.json")
    filename = EXPECTED_CORPUS_FILES[0]

    source_hash = manifest.source_hash(corpus / filename)
    manifest.record_success(filename, source_hash, 12)
    reloaded = CorpusManifest(tmp_path / "processed" / "corpus_manifest.json")

    assert reloaded.sync_status(corpus, store=None)[0]["status"] == "loaded"
    assert reloaded.read()[filename]["chunks"] == 12

    (corpus / filename).write_text("Contenido cambiado", encoding="utf-8")
    assert reloaded.sync_status(corpus, store=None)[0]["status"] == "pending"


def test_manifest_records_failure_with_user_safe_message(tmp_path: Path) -> None:
    manifest = CorpusManifest(tmp_path / "processed" / "corpus_manifest.json")

    manifest.record_failure(EXPECTED_CORPUS_FILES[0], "No se pudo procesar el archivo.")

    payload = json.loads((tmp_path / "processed" / "corpus_manifest.json").read_text())
    assert payload[EXPECTED_CORPUS_FILES[0]]["status"] == "failed"
    assert (
        payload[EXPECTED_CORPUS_FILES[0]]["error"] == "No se pudo procesar el archivo."
    )


def test_manifest_persists_partial_progress_by_source_hash(tmp_path: Path) -> None:
    manifest = CorpusManifest(tmp_path / "processed" / "corpus_manifest.json")

    manifest.record_progress(
        "manual.pdf",
        "hash-a",
        status="partial",
        total_chunks=10,
        indexed_chunks=4,
        error="Cuota agotada; espere unos minutos y vuelva a intentar.",
    )

    entry = manifest.get("manual.pdf", "hash-a")
    assert entry["status"] == "partial"
    assert entry["total_chunks"] == 10
    assert entry["indexed_chunks"] == 4
    assert "Cuota" in entry["error"]


def test_manifest_status_keeps_partial_progress(tmp_path: Path) -> None:
    corpus = make_corpus(tmp_path)
    manifest = CorpusManifest(tmp_path / "processed" / "corpus_manifest.json")
    filename = EXPECTED_CORPUS_FILES[0]
    source_hash = manifest.source_hash(corpus / filename)
    manifest.record_progress(
        filename,
        source_hash,
        status="partial",
        total_chunks=10,
        indexed_chunks=4,
        error="Espere unos minutos y vuelva a intentar.",
    )

    entry = manifest.sync_status(corpus, store=None)[0]

    assert entry["status"] == "partial"
    assert entry["total_chunks"] == 10
    assert entry["indexed_chunks"] == 4
