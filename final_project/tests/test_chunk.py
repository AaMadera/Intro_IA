import pytest

from app.chunk import chunk_text


def test_chunks_words_with_overlap_and_preserves_accents() -> None:
    text = "área uno dos tres cuatro cinco seis"

    chunks = chunk_text(text, size=4, overlap=1)

    assert chunks == ["área uno dos tres", "tres cuatro cinco seis"]


def test_chunking_is_deterministic_and_has_no_empty_chunks() -> None:
    text = "uno dos tres cuatro cinco"

    first = chunk_text(text, size=3, overlap=1)

    assert first == chunk_text(text, size=3, overlap=1)
    assert all(first)


@pytest.mark.parametrize("size, overlap", [(0, 0), (3, -1), (3, 3), (3, 4)])
def test_rejects_invalid_size_or_overlap(size: int, overlap: int) -> None:
    with pytest.raises(ValueError):
        chunk_text("uno dos tres", size=size, overlap=overlap)
