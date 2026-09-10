from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class StopReason(str, Enum):
    final_answer = "final_answer"
    iteration_limit = "iteration_limit"
    timeout = "timeout"
    parse_error = "parse_error"
    tool_error = "tool_error"


class AgentRequest(BaseModel):
    query: str = Field(
        ...,
        description="The question to ask the research assistant agent.",
        examples=["What is the population of France divided by the area of Germany?"],
        min_length=1,
        max_length=1000,
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier to group related queries.",
        examples=["session-abc123"],
    )
    max_iterations: int = Field(
        default=10,
        ge=1,
        le=25,
        description="Maximum number of ReAct loop iterations before giving up.",
        examples=[10],
    )
    return_trace: bool = Field(
        default=True,
        description="Whether to include the full step-by-step trace in the response.",
        examples=[True],
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Query must not be empty or whitespace only.")
        return v


class ThoughtStep(BaseModel):
    step_number: int = Field(..., description="Index of this loop iteration, starting at 1.", examples=[1])
    thought: str = Field(..., description="The model's reasoning text for this step.", examples=["I need to search for the population of France."])
    tool: Optional[str] = Field(default=None, description="The tool name chosen for this step, if any.", examples=["search"])
    tool_input: Optional[str] = Field(default=None, description="The input passed to the tool.", examples=["population of France"])
    observation: Optional[str] = Field(default=None, description="The result returned by the tool.", examples=["The population of France is approximately 68,170,000."])


class AgentResponse(BaseModel):
    final_answer: str = Field(..., description="The agent's final answer to the query.", examples=["Approximately 191 people per square kilometre."])
    trace: list[ThoughtStep] = Field(default_factory=list, description="Step-by-step reasoning trace, if requested.")
    iterations: int = Field(..., description="Number of loop iterations actually taken.", examples=[3])
    latency_ms: float = Field(..., description="End-to-end latency in milliseconds.", examples=[1523.4])
    stop_reason: StopReason = Field(..., description="Machine-readable reason the loop ended.", examples=["final_answer"])



class ConversationTurnResponse(BaseModel):
    """One completed conversation turn returned by the history endpoint."""

    query: str = Field(
        ...,
        description="The user's original query for this turn.",
        examples=["What is the default retention for Team projects?"],
    )
    answer: str = Field(
        ...,
        description="The final answer returned by the agent for this turn.",
        examples=["The pricing FAQ says the advertised default is 90 days."],
    )
    timestamp: datetime = Field(
        ...,
        description="UTC timestamp recorded after the agent completed the turn.",
        examples=["2026-09-10T08:30:00+00:00"],
    )


class AgentHistoryResponse(BaseModel):
    """Conversation history for one known session."""

    session_id: str = Field(
        ...,
        description="Session identifier whose stored turns are returned.",
        examples=["session-abc123"],
    )
    turns: list[ConversationTurnResponse] = Field(
        default_factory=list,
        description="Completed turns ordered from oldest to newest.",
    )