import hashlib
from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app import extract


def test_extracts_text_and_markdown_to_utf8_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "nota.md"
    source.write_text("Cultivo de chile habanero: información útil.", encoding="utf-8")

    document = extract.extract_document(source, tmp_path / "processed")

    assert document.source_name == "nota.md"
    assert document.text == "Cultivo de chile habanero: información útil."
    assert document.processed_path.read_text(encoding="utf-8") == document.text
    assert document.source_sha256 == hashlib.sha256(source.read_bytes()).hexdigest()


def test_pdf_falls_back_to_pypdf_when_opendataloader_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "manual.pdf"
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): writer._add_object(font)}
            )
        }
    )
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 20 100 Td (Cultivo) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(content)
    with source.open("wb") as file:
        writer.write(file)

    def unavailable(_: Path) -> object:
        raise FileNotFoundError("opendataloader-pdf is unavailable")

    monkeypatch.setattr(extract, "_extract_with_opendataloader", unavailable)

    document = extract.extract_document(source, tmp_path / "processed")

    assert document.source_name == "manual.pdf"
    assert document.processed_path.exists()
    assert document.pages
    assert document.pages[0]["page"] == 1


def test_pdf_reports_both_extractor_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "broken.pdf"
    source.write_bytes(b"not a pdf")

    def opendataloader_failed(_: Path) -> object:
        raise RuntimeError("converter failed")

    def pypdf_failed(_: Path) -> object:
        raise ValueError("invalid structure")

    monkeypatch.setattr(extract, "_extract_with_opendataloader", opendataloader_failed)
    monkeypatch.setattr(extract, "_extract_with_pypdf", pypdf_failed)

    with pytest.raises(extract.DocumentExtractionError) as error:
        extract.extract_document(source, tmp_path / "processed")

    assert "OpenDataLoader" in str(error.value)
    assert "converter failed" in str(error.value)
    assert "pypdf" in str(error.value)
    assert "invalid structure" in str(error.value)


def test_rejects_empty_extraction(tmp_path: Path) -> None:
    source = tmp_path / "empty.txt"
    source.write_text("   \n", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        extract.extract_document(source, tmp_path / "processed")


def test_reuses_cached_extraction_and_page_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "nota.txt"
    source.write_text("Texto cacheado.", encoding="utf-8")
    calls = 0
    original = extract._read_source

    def counted_read(path: Path) -> tuple[str, list[dict[str, object]]]:
        nonlocal calls
        calls += 1
        return original(path)

    monkeypatch.setattr(extract, "_read_source", counted_read)
    first = extract.extract_document(source, tmp_path / "processed")
    second = extract.extract_document(source, tmp_path / "processed")
    renamed_source = tmp_path / "renamed.txt"
    renamed_source.write_bytes(source.read_bytes())
    third = extract.extract_document(renamed_source, tmp_path / "processed")

    assert calls == 1
    assert second.text == first.text
    assert second.pages == first.pages
    assert third.text == first.text
