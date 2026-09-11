from dataclasses import dataclass
from datetime import UTC, datetime
import re
from pathlib import Path

import chromadb


CORPUS_PATH = Path("corpus")
CHROMA_PATH = Path("chroma_db")
COLLECTION_NAME = "research_corpus"
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 150
DEFAULT_RESULT_COUNT = 3

_collection = None


@dataclass
class RetrievedChunk:
    """One chunk returned from the local ChromaDB collection."""

    chunk_id: str
    source: str
    chunk_index: int
    text: str
    distance: float


def _load_corpus_documents(corpus_path: Path) -> list[tuple[str, str]]:
    """Load non-empty Markdown documents from the corpus directory."""

    if not corpus_path.exists():
        raise ValueError(f"Corpus directory does not exist: {corpus_path}")

    documents: list[tuple[str, str]] = []

    for file_path in sorted(corpus_path.glob("*.md")):
        text = file_path.read_text(encoding="utf-8").strip()

        if text:
            documents.append((file_path.name, text))

    if not documents:
        raise ValueError("No non-empty Markdown documents were found.")

    return documents


def _split_text(text: str) -> list[str]:
    """Split text into overlapping chunks without starting inside a word."""

    if CHUNK_OVERLAP >= CHUNK_SIZE:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")

    text = text.strip()

    if not text:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))

        if end < len(text):
            boundary = text.rfind(" ", start, end)

            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        next_start = max(end - CHUNK_OVERLAP, start + 1)

        while next_start < len(text) and not text[next_start].isspace():
            next_start += 1

        start = next_start


    return chunks


def create_or_load_collection(
    corpus_path: Path = CORPUS_PATH,
    chroma_path: Path = CHROMA_PATH,
):
    """Create/load the local collection and idempotently seed corpus chunks."""

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, str | int]] = []

    for filename, text in _load_corpus_documents(corpus_path):
        file_stem = Path(filename).stem

        for chunk_index, chunk in enumerate(_split_text(text)):
            ids.append(f"{file_stem}-chunk-{chunk_index}")
            documents.append(chunk)
            metadatas.append(
                {
                    "source": filename,
                    "chunk_index": chunk_index,
                }
            )

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    return collection


def initialize_retrieval() -> None:
    """Create or load the local ChromaDB collection at application startup."""

    global _collection

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    _collection = client.get_or_create_collection(name=COLLECTION_NAME)


def retrieve(
    query: str,
    result_count: int = DEFAULT_RESULT_COUNT,
    source_filename: str | None = None,
) -> tuple[list[RetrievedChunk], int]:
    """Return similar chunks, optionally restricted to one source document."""

    query = query.strip()

    if not query:
        raise ValueError("Query cannot be empty.")

    if result_count < 1:
        raise ValueError("Result count must be at least 1.")

    if source_filename is not None:
        source_filename = source_filename.strip()

        if not source_filename:
            raise ValueError("Source filename cannot be empty.")

    if _collection is None:
        raise RuntimeError("Retrieval collection has not been initialized.")

    where = {"source": source_filename} if source_filename else None

    total_chunks = _collection.count() if where is None else len(
        _collection.get(where=where, include=[])["ids"]
    )

    if total_chunks == 0:
        return [], 0

    n_results = min(result_count, total_chunks)

    query_arguments = {
        "query_texts": [query],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }

    if where is not None:
        query_arguments["where"] = where

    response = _collection.query(**query_arguments)

    chunk_ids = response["ids"][0]
    documents = response["documents"][0]
    metadatas = response["metadatas"][0]
    distances = response["distances"][0]

    results: list[RetrievedChunk] = []

    for chunk_id, document, metadata, distance in zip(
        chunk_ids,
        documents,
        metadatas,
        distances,
        strict=True,
    ):
        results.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                source=str(metadata["source"]),
                chunk_index=int(metadata["chunk_index"]),
                text=document,
                distance=float(distance),
            )
        )

    return results, total_chunks


def ingest_document(
    filename: str,
    text: str,
) -> tuple[str, int, int, int, bool]:
    """Chunk and store one document, replacing an existing matching source."""

    if _collection is None:
        raise RuntimeError("Retrieval collection has not been initialized.")

    filename = Path(filename).name.strip()
    text = text.strip()

    if not filename:
        raise ValueError("Filename cannot be empty.")

    if not text:
        raise ValueError("Document content cannot be empty.")

    document_id = re.sub(r"[^a-z0-9]+", "-", Path(filename).stem.lower()).strip("-")

    if not document_id:
        raise ValueError("Filename must contain at least one letter or number.")

    existing = _collection.get(
        where={"source": filename},
        include=[],
    )
    existing_ids = existing["ids"]
    replaced_existing = len(existing_ids) > 0

    if existing_ids:
        _collection.delete(ids=existing_ids)

    ingested_at = datetime.now(UTC).isoformat()
    chunks = _split_text(text)

    if not chunks:
        raise ValueError("Document content did not produce any chunks.")

    chunk_ids = [
        f"{document_id}-chunk-{chunk_index}"
        for chunk_index in range(len(chunks))
    ]
    metadatas = [
        {
            "source": filename,
            "document_id": document_id,
            "chunk_index": chunk_index,
            "ingested_at": ingested_at,
        }
        for chunk_index in range(len(chunks))
    ]

    _collection.upsert(
        ids=chunk_ids,
        documents=chunks,
        metadatas=metadatas,
    )

    all_metadata = _collection.get(include=["metadatas"])["metadatas"]
    total_documents = len(
        {
            str(metadata["source"])
            for metadata in all_metadata
            if metadata is not None
        }
    )

    return (
        document_id,
        len(chunks),
        _collection.count(),
        total_documents,
        replaced_existing,
    )