from fastapi import APIRouter, HTTPException, status

from react_research_assistant.models.calculator import (
    CalculateRequest,
    CalculateResponse,
)
from react_research_assistant.services.calculator import (
    CalculatorError,
    calculate,
)


router = APIRouter()


@router.post(
    "/calculate",
    response_model=CalculateResponse,
    summary="Calculate a basic arithmetic expression",
)
def calculate_expression(request: CalculateRequest) -> CalculateResponse:
    """Calculate a safe basic arithmetic expression."""

    try:
        result = calculate(request.expression)
    except CalculatorError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return CalculateResponse(
        expression=request.expression,
        result=result,
    )