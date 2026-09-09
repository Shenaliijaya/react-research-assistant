from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AgentRequest(BaseModel):
    """Request contract for the future ReAct agent endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Question or task for the research assistant.",
        examples=["What is the retention period for new Team projects?"],
    )
    session_id: str | None = Field(
        default=None,
        max_length=100,
        description="Optional identifier used to associate related agent requests.",
        examples=["demo-session-001"],
    )
    max_iterations: int = Field(
        default=10,
        ge=1,
        le=25,
        description="Maximum number of reasoning and tool-use iterations allowed.",
        examples=[10],
    )
    include_trace: bool = Field(
        default=False,
        description="Whether the response should include the agent reasoning and tool trace.",
        examples=[False],
    )

    @field_validator("query")
    @classmethod
    def strip_and_validate_query(cls, value: str) -> str:
        """Strip outer whitespace and reject an empty result."""

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Query cannot be empty or whitespace only.")

        return cleaned


class ThoughtStep(BaseModel):
    """One observable ReAct loop iteration."""

    step_number: int = Field(
        ...,
        ge=1,
        description="One-based position of this step in the agent loop.",
        examples=[1],
    )
    thought: str = Field(
        ...,
        description="The agent's reasoning for the next action.",
        examples=["I need the retention policy, so I should retrieve relevant documents."],
    )
    tool_name: str | None = Field(
        default=None,
        description="Name of the tool selected for this step, if a tool was used.",
        examples=["retrieve"],
    )
    tool_input: str | None = Field(
        default=None,
        description="Input given to the selected tool, if a tool was used.",
        examples=["default retention for new Team projects"],
    )
    observation: str | None = Field(
        default=None,
        description="Result observed after calling the tool, if a tool was used.",
        examples=["The default advertised retention for new Team projects is 90 days."],
    )


class AgentResponse(BaseModel):
    """Response contract for the future ReAct agent endpoint."""

    final_answer: str = Field(
        ...,
        description="The final answer produced by the agent.",
        examples=["New Team projects have a default advertised retention period of 90 days."],
    )
    trace: list[ThoughtStep] = Field(
        default_factory=list,
        description="Reasoning and tool-use steps, included when requested.",
        examples=[[]],
    )
    iteration_count: int = Field(
        ...,
        ge=0,
        description="Number of reasoning iterations completed before the loop ended.",
        examples=[2],
    )
    latency_ms: float = Field(
        ...,
        ge=0,
        description="End-to-end request processing time in milliseconds.",
        examples=[245.6],
    )
    end_reason: Literal[
        "final_answer",
        "iteration_limit",
        "parser_error",
        "tool_error",
    ] = Field(
        ...,
        description="Machine-readable reason the agent loop ended.",
        examples=["final_answer"],
    )