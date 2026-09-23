from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
import hashlib
import json
import re

import chromadb
import pymupdf


CORPUS_PATH = Path("corpus")
CHROMA_PATH = Path("chroma_db")
TABLE_ARTIFACTS_PATH = Path("data/table_artifacts")

COLLECTION_NAME = "research_corpus"

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 150
DEFAULT_RESULT_COUNT = 3

SUPPORTED_DOCUMENT_SUFFIXES = {".md", ".txt", ".pdf"}

_collection = None


@dataclass(frozen=True)
class ExtractedPage:
    """Text extracted from one uploaded document page or text file."""

    text: str
    page_number: int | None
    extraction_method: str


@dataclass(frozen=True)
class ExtractedTable:
    """One accepted, structured table extracted from a native-text PDF."""

    table_id: str
    page_number: int
    table_index_on_page: int
    bounding_box: list[float]
    headers: list[str]
    rows: list[dict[str, str | int]]
    raw_rows: list[list[str]]
    markdown: str


@dataclass
class RetrievedChunk:
    """One chunk returned from the local ChromaDB collection."""

    chunk_id: str
    source: str
    chunk_index: int
    text: str
    distance: float
    page_number: int | None = None
    content_type: str = "text"
    table_id: str | None = None
    row_number: int | None = None


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


def _clean_cell(value: str | None) -> str:
    """Convert PDF cells to normalized strings."""

    if value is None:
        return ""

    return " ".join(str(value).split())


def _make_unique_headers(raw_header_row: list[str | None]) -> list[str]:
    """
    Return safe, unique headers.

    Example:
    ['Rate', 'Rate', None] becomes ['Rate', 'Rate_2', 'column_3'].
    """

    headers: list[str] = []
    used: dict[str, int] = {}

    for column_number, value in enumerate(raw_header_row, start=1):
        base_name = _clean_cell(value) or f"column_{column_number}"

        used[base_name] = used.get(base_name, 0) + 1
        occurrence = used[base_name]

        headers.append(
            base_name if occurrence == 1 else f"{base_name}_{occurrence}"
        )

    return headers


def _is_regular_table(raw_rows: list[list[str | None]]) -> tuple[bool, str]:
    """
    Accept only simple header + row tables.

    This is intentionally conservative. Complex layouts, merged-cell forms,
    blank headers, or inconsistent rows are not indexed as trusted table rows.
    """

    if len(raw_rows) < 2:
        return False, "Needs one header row and at least one data row."

    header_row = raw_rows[0]

    if len(header_row) < 2:
        return False, "Needs at least two columns."

    clean_headers = [_clean_cell(cell) for cell in header_row]

    if any(not header for header in clean_headers):
        return False, "One or more header cells are blank."

    if len(set(clean_headers)) != len(clean_headers):
        return False, "One or more headers are repeated."

    expected_column_count = len(header_row)
    usable_row_count = 0

    for row in raw_rows[1:]:
        clean_row = [_clean_cell(cell) for cell in row]

        if not any(clean_row):
            continue

        usable_row_count += 1

        if len(row) != expected_column_count:
            return False, "A data row has a different number of columns."

    if usable_row_count == 0:
        return False, "No usable data rows were found."

    return True, "Accepted."


def _rows_to_records(
    headers: list[str],
    raw_data_rows: list[list[str | None]],
) -> list[dict[str, str | int]]:
    """Convert table rows into header/value dictionaries."""

    records: list[dict[str, str | int]] = []

    for row_number, row in enumerate(raw_data_rows, start=1):
        clean_row = [_clean_cell(cell) for cell in row]

        if not any(clean_row):
            continue

        record: dict[str, str | int] = {
            header: clean_row[column_index]
            for column_index, header in enumerate(headers)
        }
        record["__row_number"] = row_number

        records.append(record)

    return records


def _safe_artifact_name(value: str) -> str:
    """Create a safe file/folder component."""

    return re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("._") or "document"


def _document_hash(content: bytes) -> str:
    """Return a stable SHA-256 hash for the exact uploaded file."""

    return hashlib.sha256(content).hexdigest()


def _save_json(path: Path, value: dict) -> None:
    """Write one UTF-8 JSON file."""

    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _extract_text_document(content: bytes) -> list[ExtractedPage]:
    """Decode one UTF-8 Markdown or plain-text upload."""

    try:
        text = content.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise ValueError("Markdown and text files must be valid UTF-8.") from exc

    if not text:
        raise ValueError("Document content cannot be empty.")

    return [
        ExtractedPage(
            text=text,
            page_number=None,
            extraction_method="native_text",
        )
    ]


def _extract_pdf_document(
    content: bytes,
) -> tuple[list[ExtractedPage], list[ExtractedTable]]:
    """
    Extract normal page text and accepted structured tables from one PDF.

    Page text is retained because it contains normal paragraphs.
    Tables are separately represented for table-aware retrieval.
    """

    if not content:
        raise ValueError("PDF content cannot be empty.")

    try:
        document = pymupdf.open(stream=BytesIO(content), filetype="pdf")
    except Exception as exc:
        raise ValueError("The uploaded file is not a readable PDF.") from exc

    document_hash = _document_hash(content)
    pages: list[ExtractedPage] = []
    tables: list[ExtractedTable] = []

    try:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()

            if text:
                pages.append(
                    ExtractedPage(
                        text=text,
                        page_number=page_number,
                        extraction_method="native_text",
                    )
                )

            table_finder = page.find_tables()

            for table_index, table in enumerate(table_finder.tables, start=1):
                raw_rows = table.extract()
                accepted, _ = _is_regular_table(raw_rows)

                if not accepted:
                    continue

                headers = _make_unique_headers(raw_rows[0])
                rows = _rows_to_records(headers, raw_rows[1:])

                if not rows:
                    continue

                table_id = (
                    f"{document_hash[:16]}"
                    f"_page_{page_number:03d}"
                    f"_table_{table_index:03d}"
                )

                tables.append(
                    ExtractedTable(
                        table_id=table_id,
                        page_number=page_number,
                        table_index_on_page=table_index,
                        bounding_box=[float(value) for value in table.bbox],
                        headers=headers,
                        rows=rows,
                        raw_rows=[
                            [_clean_cell(cell) for cell in row]
                            for row in raw_rows
                        ],
                        markdown=table.to_markdown(),
                    )
                )
    finally:
        document.close()

    if not pages:
        raise ValueError(
            "No extractable text was found in this PDF. "
            "It may be a scanned or image-only PDF and require OCR."
        )

    return pages, tables


def _extract_uploaded_document(filename: str, content: bytes) -> list[ExtractedPage]:
    """Extract page-aware normal text from one supported uploaded document."""

    suffix = Path(filename).suffix.lower()

    if suffix not in SUPPORTED_DOCUMENT_SUFFIXES:
        raise ValueError(
            "Only Markdown (.md), text (.txt), and PDF (.pdf) files are supported."
        )

    if suffix == ".pdf":
        pages, _ = _extract_pdf_document(content)
        return pages

    return _extract_text_document(content)


def _store_table_artifacts(
    filename: str,
    document_id: str,
    content: bytes,
    tables: list[ExtractedTable],
    ingested_at: str,
) -> None:
    """
    Save the durable JSON and Markdown versions of accepted PDF tables.

    These files are the structured source of truth.
    ChromaDB holds retrieval text, not the only copy of table structure.
    """

    document_hash = _document_hash(content)
    document_folder = TABLE_ARTIFACTS_PATH / _safe_artifact_name(document_id)

    if document_folder.exists():
        for old_file in document_folder.glob("*"):
            old_file.unlink()
    else:
        document_folder.mkdir(parents=True, exist_ok=True)

    for table in tables:
        file_prefix = (
            f"page_{table.page_number:03d}_"
            f"table_{table.table_index_on_page:03d}"
        )

        markdown_filename = f"{file_prefix}.md"
        json_filename = f"{file_prefix}.json"

        artifact = {
            "table_id": table.table_id,
            "document_id": document_id,
            "source_filename": filename,
            "source_file_sha256": document_hash,
            "page_number": table.page_number,
            "table_index_on_page": table.table_index_on_page,
            "bounding_box": table.bounding_box,
            "extraction_method": "pymupdf_native_find_tables",
            "quality_status": "accepted",
            "ingested_at": ingested_at,
            "headers": table.headers,
            "row_count": len(table.rows),
            "rows": table.rows,
            "raw_rows": table.raw_rows,
            "markdown_file": markdown_filename,
        }

        _save_json(document_folder / json_filename, artifact)

        (document_folder / markdown_filename).write_text(
            table.markdown,
            encoding="utf-8",
        )


def _make_table_summary_chunk(
    table: ExtractedTable,
    source_filename: str,
) -> str:
    """Create one readable retrieval document for the whole table."""

    return "\n".join(
        [
            f"Table from: {source_filename}",
            f"Page: {table.page_number}",
            f"Table number on page: {table.table_index_on_page}",
            "",
            table.markdown.strip(),
        ]
    )


def _make_table_row_chunk(
    table: ExtractedTable,
    record: dict[str, str | int],
    source_filename: str,
) -> str:
    """Create one compact, semantically clear retrieval document for one row."""

    lines = [
        f"Table from: {source_filename}",
        f"Page: {table.page_number}",
        f"Table number on page: {table.table_index_on_page}",
        "Table row:",
    ]

    for header in table.headers:
        lines.append(f"{header}: {record[header]}")

    return "\n".join(lines)


def create_or_load_collection(
    corpus_path: Path = CORPUS_PATH,
    chroma_path: Path = CHROMA_PATH,
):
    """Create/load the local collection and idempotently seed Markdown corpus chunks."""

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
                    "content_type": "text",
                }
            )

    if ids:
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
    """Return similar text or table chunks, optionally restricted to one source."""

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

    total_chunks = (
        _collection.count()
        if where is None
        else len(_collection.get(where=where, include=[])["ids"])
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
        page_value = metadata.get("page_number")
        row_value = metadata.get("row_number")

        results.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                source=str(metadata["source"]),
                chunk_index=int(metadata["chunk_index"]),
                text=document,
                distance=float(distance),
                page_number=int(page_value) if page_value is not None else None,
                content_type=str(metadata.get("content_type", "text")),
                table_id=(
                    str(metadata["table_id"])
                    if metadata.get("table_id") is not None
                    else None
                ),
                row_number=int(row_value) if row_value is not None else None,
            )
        )

    return results, total_chunks


def ingest_document(
    filename: str,
    content: bytes,
) -> tuple[str, int, int, int, bool]:
    """Extract, table-process, chunk, and store one document."""

    if _collection is None:
        raise RuntimeError("Retrieval collection has not been initialized.")

    filename = Path(filename).name.strip()

    if not filename:
        raise ValueError("Filename cannot be empty.")

    suffix = Path(filename).suffix.lower()

    if suffix not in SUPPORTED_DOCUMENT_SUFFIXES:
        raise ValueError(
            "Only Markdown (.md), text (.txt), and PDF (.pdf) files are supported."
        )

    document_id = re.sub(
        r"[^a-z0-9]+",
        "-",
        Path(filename).stem.lower(),
    ).strip("-")

    if not document_id:
        raise ValueError("Filename must contain at least one letter or number.")

    extracted_pages: list[ExtractedPage]
    extracted_tables: list[ExtractedTable] = []

    if suffix == ".pdf":
        extracted_pages, extracted_tables = _extract_pdf_document(content)
    else:
        extracted_pages = _extract_text_document(content)

    existing = _collection.get(
        where={"source": filename},
        include=[],
    )
    existing_ids = existing["ids"]
    replaced_existing = len(existing_ids) > 0

    if existing_ids:
        _collection.delete(ids=existing_ids)

    ingested_at = datetime.now(UTC).isoformat()

    if suffix == ".pdf":
        _store_table_artifacts(
            filename=filename,
            document_id=document_id,
            content=content,
            tables=extracted_tables,
            ingested_at=ingested_at,
        )

    chunk_ids: list[str] = []
    chunks: list[str] = []
    metadatas: list[dict[str, str | int]] = []

    chunk_index = 0

    # 1. Store normal page text as ordinary text chunks.
    for extracted_page in extracted_pages:
        for chunk in _split_text(extracted_page.text):
            chunk_ids.append(f"{document_id}-text-{chunk_index}")
            chunks.append(chunk)

            metadata: dict[str, str | int] = {
                "source": filename,
                "document_id": document_id,
                "chunk_index": chunk_index,
                "content_type": "text",
                "extraction_method": extracted_page.extraction_method,
                "ingested_at": ingested_at,
            }

            if extracted_page.page_number is not None:
                metadata["page_number"] = extracted_page.page_number

            metadatas.append(metadata)
            chunk_index += 1

    # 2. Store one whole-table summary and one retrieval document per row.
    for table in extracted_tables:
        summary_chunk = _make_table_summary_chunk(
            table=table,
            source_filename=filename,
        )

        chunk_ids.append(f"{document_id}-table-summary-{table.table_id}")
        chunks.append(summary_chunk)
        metadatas.append(
            {
                "source": filename,
                "document_id": document_id,
                "chunk_index": chunk_index,
                "content_type": "table_summary",
                "table_id": table.table_id,
                "page_number": table.page_number,
                "table_index_on_page": table.table_index_on_page,
                "extraction_method": "pymupdf_native_find_tables",
                "ingested_at": ingested_at,
            }
        )
        chunk_index += 1

        for record in table.rows:
            row_number = int(record["__row_number"])

            row_chunk = _make_table_row_chunk(
                table=table,
                record=record,
                source_filename=filename,
            )

            chunk_ids.append(
                f"{document_id}-table-row-{table.table_id}-row-{row_number}"
            )
            chunks.append(row_chunk)
            metadatas.append(
                {
                    "source": filename,
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "content_type": "table_row",
                    "table_id": table.table_id,
                    "row_number": row_number,
                    "page_number": table.page_number,
                    "table_index_on_page": table.table_index_on_page,
                    "extraction_method": "pymupdf_native_find_tables",
                    "ingested_at": ingested_at,
                }
            )
            chunk_index += 1

    if not chunks:
        raise ValueError("Document content did not produce any chunks.")

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


def get_collection_stats() -> tuple[int, int]:
    """Return the live ChromaDB chunk count and unique-source count."""

    if _collection is None:
        raise RuntimeError("Retrieval collection has not been initialized.")

    chunk_count = _collection.count()

    metadata_items = _collection.get(
        include=["metadatas"],
    )["metadatas"]

    document_count = len(
        {
            str(metadata["source"])
            for metadata in metadata_items
            if metadata is not None and "source" in metadata
        }
    )

    return chunk_count, document_count