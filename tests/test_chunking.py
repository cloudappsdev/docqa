from docqa.ingest.chunking import chunk_text


def _doc(n: int) -> str:
    return "\n\n".join(f"Paragraph {i}. " + "word " * 18 for i in range(n))


def test_short_text_is_one_chunk():
    assert len(chunk_text("Hello world.\n\nSecond para.", 500, 100)) == 1


def test_chunks_respect_max_size():
    chunks = chunk_text(_doc(30), max_chars=500, overlap=150)
    assert len(chunks) > 1
    assert all(len(c) <= 500 for c in chunks)


def test_consecutive_chunks_overlap():
    chunks = chunk_text(_doc(30), max_chars=500, overlap=150)
    last_para = chunks[0].split("\n\n")[-1]
    assert last_para in chunks[1]


def test_no_text_is_lost():
    text = _doc(30)
    joined = "\n".join(chunk_text(text, max_chars=500, overlap=150))
    assert all(f"Paragraph {i}." in joined for i in range(30))


def test_oversized_paragraph_is_split():
    chunks = chunk_text("A sentence here. " * 200, max_chars=300, overlap=50)
    assert len(chunks) > 1 and all(len(c) <= 300 for c in chunks)


def test_empty_input():
    assert chunk_text("  \n\n  ") == []
