"""Document library with keyword search (BM25): the 'retrieval' half of retrieval-augmented generation.

No embeddings or vector database needed to start. For a few hundred reports, keyword search with good
chunking works well and is easy to explain and audit. Swap in Azure AI Search or embeddings later.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .text import normalise

STOPWORDS = set(
    "the a an and or of to in on for is are be by with as at that this it its from how what which will does do "
    "has have was were their they our we can could would should into about whether say says".split()
)


def tokenise(text: str) -> list[str]:
    words = normalise(text).replace("artificial intelligence", "ai").split()
    out = []
    for w in words:
        if (len(w) > 2 or w == "ai") and w not in STOPWORDS:
            out.append(re.sub(r"(ing|ed|es|s)$", "", w) if len(w) > 4 else w)
    return out


@dataclass
class Passage:
    id: str
    source: str
    where: str
    text: str


def chunk_text(text: str, max_chars: int = 900) -> list[str]:
    """Split text into passages of whole sentences, each up to about max_chars characters."""
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.findall(r"[^.!?]+[.!?]+|[^.!?]+$", text)
    chunks, current = [], ""
    for s in sentences:
        if current and len(current) + len(s) > max_chars:
            chunks.append(current.strip())
            current = ""
        current += s
    if current.strip():
        chunks.append(current.strip())
    return chunks


class Library:
    def __init__(self):
        self.passages: list[Passage] = []

    def add_text(self, source: str, text: str, where_prefix: str = "passage") -> int:
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks, start=1):
            self.passages.append(Passage(f"P{len(self.passages) + 1}", source, f"{where_prefix} {i}", chunk))
        return len(chunks)

    def add_pdf(self, path: str | Path) -> int:
        from pypdf import PdfReader

        path = Path(path)
        added = 0
        for page_no, page in enumerate(PdfReader(str(path)).pages, start=1):
            for chunk in chunk_text(page.extract_text() or ""):
                if len(chunk) < 80:  # skip headers, footers and page furniture
                    continue
                self.passages.append(Passage(f"P{len(self.passages) + 1}", path.stem, f"p.{page_no}", chunk))
                added += 1
        return added

    def add_markdown(self, source: str, text: str) -> int:
        """Markdown notes: each '## heading' section becomes passages labelled with that heading."""
        added = 0
        for section in re.split(r"^## ", text, flags=re.M)[1:]:
            heading, _, body = section.partition("\n")
            for chunk in chunk_text(body):
                self.passages.append(Passage(f"P{len(self.passages) + 1}", source, heading.strip(), chunk))
                added += 1
        return added or self.add_text(source, text)

    def add_folder(self, folder: str | Path) -> int:
        total = 0
        for p in sorted(Path(folder).glob("*")):
            if p.suffix.lower() == ".pdf":
                total += self.add_pdf(p)
            elif p.suffix.lower() == ".md":
                total += self.add_markdown(p.stem, p.read_text(encoding="utf-8"))
            elif p.suffix.lower() == ".txt":
                total += self.add_text(p.stem, p.read_text(encoding="utf-8"))
        return total

    def search(self, query: str, k: int = 5) -> list[Passage]:
        docs = [tokenise(p.text + " " + p.where) for p in self.passages]
        if not docs:
            return []
        n, avg = len(docs), sum(map(len, docs)) / len(docs)
        df = Counter(w for d in docs for w in set(d))
        q = tokenise(query)
        scored = []
        for passage, d in zip(self.passages, docs):
            tf = Counter(d)
            score = 0.0
            for w in q:
                if tf[w]:
                    idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
                    score += idf * tf[w] * 2.2 / (tf[w] + 1.2 * (0.25 + 0.75 * len(d) / avg))
            if score > 0:
                scored.append((score, passage))
        scored.sort(key=lambda x: -x[0])
        return [p for _, p in scored[:k]]
