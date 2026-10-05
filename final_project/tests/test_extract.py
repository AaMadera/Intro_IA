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


def test_rejects_empty_extraction(tmp_path: Path) -> None:
    source = tmp_path / "empty.txt"
    source.write_text("   \n", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        extract.extract_document(source, tmp_path / "processed")
