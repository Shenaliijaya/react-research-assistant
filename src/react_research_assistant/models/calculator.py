from pydantic import BaseModel, Field


class CalculateRequest(BaseModel):
    """Request body for a calculator operation."""

    expression: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="A basic arithmetic expression using +, -, *, /, and parentheses.",
        examples=["(12 + 8) * 3"],
    )


class CalculateResponse(BaseModel):
    """Successful calculator response."""

    expression: str = Field(
        ...,
        description="The arithmetic expression that was calculated.",
        examples=["(12 + 8) * 3"],
    )
    result: int | float = Field(
        ...,
        description="The calculated numeric result.",
        examples=[60],
    )