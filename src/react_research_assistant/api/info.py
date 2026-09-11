import os

from fastapi import APIRouter
from pydantic import BaseModel, Field

from react_research_assistant.agent.factory import build_tools
from react_research_assistant.models.agent import AgentRequest


router = APIRouter()


class ToolInfo(BaseModel):
    name: str = Field(
        ...,
        description="Registered ReAct tool name.",
        examples=["retrieve"],
    )
    description: str = Field(
        ...,
        description="Live tool description supplied to the model.",
        examples=["Use this for questions about Tideline or Halcyon Labs."],
    )


class AgentInfoResponse(BaseModel):
    model: str = Field(
        ...,
        description="Configured LLM model name.",
        examples=["gemini-3.5-flash-lite"],
    )
    temperature: float = Field(
        ...,
        description="Sampling temperature used for LLM calls.",
        examples=[0.0],
    )
    default_max_iterations: int = Field(
        ...,
        description="Default maximum ReAct iterations from AgentRequest.",
        examples=[10],
    )
    minimum_max_iterations: int = Field(
        ...,
        description="Minimum permitted max_iterations value.",
        examples=[1],
    )
    maximum_max_iterations: int = Field(
        ...,
        description="Maximum permitted max_iterations value.",
        examples=[25],
    )
    timeout_seconds: int = Field(
        ...,
        description="Configured AgentExecutor execution timeout in seconds.",
        examples=[60],
    )
    tools: list[ToolInfo] = Field(
        ...,
        description="Tools read from the live agent tool registry.",
    )


@router.get(
    "/info",
    response_model=AgentInfoResponse,
    summary="Show live agent configuration",
)
def agent_info() -> AgentInfoResponse:
    """Return live tool registry and active model/agent limits."""

    tools = build_tools()

    max_iterations_field = AgentRequest.model_fields["max_iterations"]

    return AgentInfoResponse(
        model=os.getenv("LLM_MODEL", "gemini-3.5-flash-lite"),
        temperature=0.0,
        default_max_iterations=max_iterations_field.default,
        minimum_max_iterations=max_iterations_field.metadata[0].ge,
        maximum_max_iterations=max_iterations_field.metadata[1].le,
        timeout_seconds=60,
        tools=[
            ToolInfo(
                name=tool.name,
                description=tool.description,
            )
            for tool in tools
        ],
    )