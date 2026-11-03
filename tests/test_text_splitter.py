from scripts.rag_ingest import split_text


def test_empty_text_returns_no_chunks() -> None:
    assert split_text("") == []
    assert split_text("   \n\n  ") == []


def test_short_text_is_one_chunk() -> None:
    chunks = split_text("La bodega abre de lunes a sábado.", max_chars=200, overlap=20)
    assert chunks == ["La bodega abre de lunes a sábado."]


def test_chunks_respect_max_size_and_are_not_empty() -> None:
    text = "\n\n".join(f"Párrafo número {index}. " * 20 for index in range(30))
    chunks = split_text(text, max_chars=300, overlap=50)
    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)
    assert all(len(chunk) <= 300 for chunk in chunks)


def test_invalid_overlap_is_rejected() -> None:
    for overlap in (-1, 100):
        try:
            split_text("texto", max_chars=100, overlap=overlap)
        except ValueError:
            pass
        else:
            raise AssertionError(f"overlap={overlap} should raise ValueError")
