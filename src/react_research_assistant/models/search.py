from pydantic import BaseModel, Field, field_validator

class SearchRequest(BaseModel):
    """Request body for fact-table search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Text used to search the supplied fact table.",
        examples=["area of Germany"],
    )

    @field_validator("query")
    @classmethod
    def strip_and_validate_query(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Query cannot be empty or whitespace only.")

        return cleaned


class SearchResult(BaseModel):
    """One fact returned by mock search."""

    id: int = Field(
        ...,
        description="Stable identifier for the supplied fact.",
        examples=[1],
    )
    keywords: list[str] = Field(
        ...,
        description="Keywords associated with the fact.",
        examples=[["germany", "area"]],
    )
    snippet: str = Field(
        ...,
        description="Fact text returned to the caller.",
        examples=["Germany has an area of approximately 357,022 square kilometres."],
    )
    source: str = Field(
        ...,
        description="Source associated with the fact.",
        examples=["mock://worldfacts/france"],
    )

class SearchResponse(BaseModel):
    """Successful mock-search response."""

    results: list[SearchResult] = Field(
        default_factory=list,
        description="Highest-scoring matching facts, capped at five results.",
        examples=[[]],
    )