from fastapi import APIRouter, HTTPException, status

from react_research_assistant.models.retrieval import (
    RetrieveRequest,
    RetrieveResponse,
    RetrievedChunkResponse,
)
from react_research_assistant.services.retrieval import retrieve


router = APIRouter()


@router.post(
    "/retrieve",
    response_model=RetrieveResponse,
    summary="Retrieve relevant corpus chunks",
)
def retrieve_chunks(request: RetrieveRequest) -> RetrieveResponse:
    """Retrieve the most semantically similar corpus chunks."""

    try:
        chunks, total_chunks = retrieve(
            query=request.query,
            result_count=request.result_count,
            source_filename=request.source_filename,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    results = [
        RetrievedChunkResponse(
            chunk_id=chunk.chunk_id,
            source=chunk.source,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            distance=chunk.distance,
        )
        for chunk in chunks
    ]

    return RetrieveResponse(
        results=results,
        total_chunks=total_chunks,
        truncated=total_chunks > len(results),
    )