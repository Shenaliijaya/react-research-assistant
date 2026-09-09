from pydantic import BaseModel, Field, field_validator


class CalculateRequest(BaseModel):
    """Request body for a calculator operation."""

    expression: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Basic arithmetic expression using numbers, +, -, *, /, and parentheses.",
        examples=["(12 + 8) * 3"],
    )

    @field_validator("expression")
    @classmethod
    def strip_and_validate_expression(cls, value: str) -> str:
        """Strip outer whitespace and reject an empty result."""

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Expression cannot be empty or whitespace only.")

        return cleaned


class CalculateResponse(BaseModel):
    """Successful calculator response."""

    expression: str = Field(
        ...,
        description="The validated arithmetic expression that was calculated.",
        examples=["(12 + 8) * 3"],
    )
    result: int | float = Field(
        ...,
        description="The numeric result of the expression.",
        examples=[60],
    )