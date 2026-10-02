"""Document Assistant: answers questions from the library and cites a passage for every point.

The model only sees the retrieved passages, never the whole library, and the code checks that every
citation points to a passage that was actually retrieved.
"""
from __future__ import annotations

import re

from .llm import LLM
from .retrieval import Library

PROMPT = """Answer the question using ONLY the passages below. After every sentence that uses a passage, cite it like [P3].
If the passages do not answer the question, say so plainly instead of guessing. Plain text, under 200 words.

Question: {question}

Passages:
{passages}"""


def answer(question: str, library: Library, llm: LLM, k: int = 5) -> dict:
    passages = library.search(question, k=k)
    if not passages:
        return {"answer": "No passage in the library matches that question.", "passages": [], "citations": [], "invalid_citations": []}
    block = "\n".join(f"[{p.id}] ({p.source}, {p.where}) {p.text}" for p in passages)
    text = llm.complete(PROMPT.format(question=question, passages=block), max_tokens=800)
    cited = list(dict.fromkeys(re.findall(r"\[(P\d+)\]", text)))
    allowed = {p.id for p in passages}
    return {
        "answer": text,
        "passages": passages,
        "citations": [c for c in cited if c in allowed],
        "invalid_citations": [c for c in cited if c not in allowed],
    }
