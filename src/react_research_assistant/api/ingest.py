from fastapi import APIRouter, File, HTTPException, UploadFile, status

from react_research_assistant.models.ingest import IngestResponse
from react_research_assistant.services.retrieval import ingest_document

router = APIRouter()


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a Markdown document",
    description=(
        "Uploads a UTF-8 Markdown file, splits it into overlapping chunks, "
        "and stores those chunks in the local ChromaDB collection. "
        "Uploading the same filename again replaces its earlier chunks."
    ),
)
async def ingest_file(
    file: UploadFile = File(
        ...,
        description="A non-empty UTF-8 Markdown (.md) or plain-text (.txt) document.",
    ),
) -> IngestResponse:
    """Validate, read, and ingest one uploaded Markdown document."""

    filename = file.filename or ""

    if not filename.lower().endswith((".md", ".txt")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only Markdown (.md) and plain-text (.txt) files are supported.",
        )

    try:
        content = await file.read()
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file must be valid UTF-8 text.",
        ) from error

    try:
        (
            document_id,
            chunk_count,
            total_chunks,
            total_documents,
            replaced_existing,
        ) = ingest_document(
            filename=filename,
            text=text,
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