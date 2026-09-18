from fastapi import APIRouter, File, HTTPException, UploadFile, status

from react_research_assistant.models.ingest import IngestResponse
from react_research_assistant.services.retrieval import ingest_document

router = APIRouter()

SUPPORTED_UPLOAD_SUFFIXES = (".md", ".txt", ".pdf")


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a Markdown, text, or PDF document",
    description=(
        "Uploads a UTF-8 Markdown/text file or a text-based PDF, extracts text, "
        "splits it into overlapping chunks, and stores those chunks in the local "
        "ChromaDB collection. PDF chunks retain their source page number. "
        "Uploading the same filename again replaces its earlier chunks."
    ),
)
async def ingest_file(
    file: UploadFile = File(
        ...,
        description=(
            "A non-empty UTF-8 Markdown (.md), text (.txt), or text-based PDF (.pdf) document. "
            "Scanned PDFs without embedded text are not supported yet."
        ),
    ),
) -> IngestResponse:
    """Validate, read, and ingest one uploaded Markdown, text, or PDF document."""

    filename = file.filename or ""

    if not filename.lower().endswith(SUPPORTED_UPLOAD_SUFFIXES):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only Markdown (.md), plain-text (.txt), and PDF (.pdf) files are supported.",
        )

    content = await file.read()

    try:
        (
            document_id,
            chunk_count,
            total_chunks,
            total_documents,
            replaced_existing,
        ) = ingest_document(
            filename=filename,
            content=content,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return IngestResponse(
        document_id=document_id,
        source_filename=filename,
        chunk_count=chunk_count,
        total_chunks=total_chunks,
        total_documents=total_documents,
        replaced_existing=replaced_existing,
    )