from toolkit.retrieval import Library, chunk_text, tokenise


def test_chunks_keep_whole_sentences_and_respect_size():
    text = "First sentence here. " * 100
    chunks = chunk_text(text, max_chars=200)
    assert all(len(c) <= 220 for c in chunks)
    assert all(c.endswith(".") for c in chunks)


def test_tokenise_keeps_ai_and_drops_stopwords():
    tokens = tokenise("What does the plan say about Artificial Intelligence?")
    assert "ai" in tokens and "the" not in tokens


def test_search_ranks_relevant_passage_first():
    lib = Library()
    lib.add_text("doc", "Volunteers ran twelve workshops in spring. "
                        "The outcome framework will measure success using indicators every quarter.")
    lib.add_text("other", "The office moved to a new building with better parking for staff.")
    hits = lib.search("how will success be measured", k=2)
    assert hits and "framework" in hits[0].text


def test_search_returns_nothing_for_unrelated_query():
    lib = Library()
    lib.add_text("doc", "Carers need respite breaks.")
    assert lib.search("quantum chromodynamics") == []


def test_project_library_loads_with_section_labels():
    lib = Library()
    assert lib.add_folder("data/library") >= 20
    assert any("Implementation" in p.where for p in lib.passages)
    assert lib.search("measure impact methodology")[0].where.startswith(("Implementation", "Activities", "Foreword", "Appendix"))
