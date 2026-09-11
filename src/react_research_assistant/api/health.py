from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from react_research_assistant.services.retrieval import get_collection_stats


router = APIRouter()


class HealthResponse(BaseModel):
    status: str = Field(
        ...,
        description="Overall application health status.",
        examples=["ok"],
    )
    collection_size: int = Field(
        ...,
        description="Number of chunks currently stored in ChromaDB.",
        examples=[30],
    )
    checked_at: datetime = Field(
        ...,
        description="UTC time at which the datastore check completed.",
        examples=["2026-09-11T09:45:00+00:00"],
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API and ChromaDB health",
)
def health_check() -> HealthResponse:
    """Verify that the retrieval datastore can be queried."""

    try:
        collection_size, _ = get_collection_stats()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Datastore health check failed: {exc}",
        ) from exc

    return HealthResponse(
        status="ok",
        collection_size=collection_size,
        checked_at=datetime.now(UTC),
    )