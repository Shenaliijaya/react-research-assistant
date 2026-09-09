from pydantic import BaseModel, Field, field_validator


class RetrieveRequest(BaseModel):
    """Request body for corpus retrieval."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Question or search text used to retrieve relevant corpus chunks.",
        examples=["What is the default advertised retention for new Team projects?"],
    )
    result_count: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of relevant chunks to return.",
        examples=[3],
    )

    @field_validator("query")
    @classmethod
    def strip_and_validate_query(cls, value: str) -> str:
        """Strip outer whitespace and reject an empty result."""

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Query cannot be empty or whitespace only.")

        return cleaned


class RetrievedChunkResponse(BaseModel):
    """One corpus chunk returned by retrieval."""

    chunk_id: str = Field(
        ...,
        description="Stable identifier for the stored corpus chunk.",
        examples=["02-rfc-014-retention-and-downsampling-chunk-1"],
    )
    source: str = Field(
        ...,
        description="Corpus file that contained the chunk.",
        examples=["02-rfc-014-retention-and-downsampling.md"],
    )
    chunk_index: int = Field(
        ...,
        description="Zero-based position of the chunk in its source file.",
        examples=[1],
    )
    text: str = Field(
        ...,
        description="Retrieved text chunk.",
        examples=["The default advertised retention for new Team projects is 90 days."],
    )
    distance: float = Field(
        ...,
        description="ChromaDB similarity distance; lower is more similar.",
        examples=[1.05],
    )


class RetrieveResponse(BaseModel):
    """Successful retrieval response."""

    results: list[RetrievedChunkResponse] = Field(
        default_factory=list,
        description="Retrieved corpus chunks ordered by similarity.",
        examples=[[]],
    )
    total_chunks: int = Field(
        ...,
        description="Total number of chunks stored in the corpus collection.",
        examples=[52],
    )
    truncated: bool = Field(
        ...,
        description="Whether the requested result limit may have omitted additional corpus chunks.",
        examples=[True],
    )