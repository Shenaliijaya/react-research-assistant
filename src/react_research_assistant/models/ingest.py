from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    """Response returned after a document has been ingested."""

    document_id: str = Field(
        ...,
        description="Stable identifier assigned to the uploaded document.",
        examples=["01-tideline-pricing-faq"],
    )
    source_filename: str = Field(
        ...,
        description="Original filename supplied with the upload.",
        examples=["01-tideline-pricing-faq.md"],
    )
    chunk_count: int = Field(
        ...,
        description="Number of text chunks stored for this document.",
        examples=[12],
    )
    total_chunks: int = Field(
        ...,
        description="Total number of chunks currently stored in the collection.",
        examples=[48],
    )
    total_documents: int = Field(
        ...,
        description="Number of unique source documents currently stored in the collection.",
        examples=[4],
    )
    replaced_existing: bool = Field(
        ...,
        description="Whether an existing document with the same filename was replaced.",
        examples=[False],
    )