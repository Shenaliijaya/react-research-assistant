import time

from fastapi import APIRouter, HTTPException, status

from react_research_assistant.agent.factory import build_agent_executor
from react_research_assistant.models.agent import (
    AgentHistoryResponse,
    AgentRequest,
    AgentResponse,
    ConversationTurnResponse,
    StopReason,
    ThoughtStep,
)
from react_research_assistant.services.session_store import (
    add_turn,
    format_recent_history,
    get_turns,
)

router = APIRouter()


@router.post("/query", response_model=AgentResponse)
def run_agent(request: AgentRequest) -> AgentResponse:
    """Run the ReAct agent and save completed turns for a supplied session."""

    start = time.perf_counter()
    conversation_history = (
        format_recent_history(request.session_id)
        if request.session_id is not None
        else "No previous conversation turns."
    )
    executor = build_agent_executor(
        max_iterations=request.max_iterations,
        timeout_seconds=60,
    )

    try:
        result = executor.invoke(
            {
                "input": request.query,
                "conversation_history": conversation_history,
            }
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return AgentResponse(
            final_answer=f"The agent failed to complete: {exc}",
            trace=[],
            iterations=0,
            latency_ms=latency_ms,
            stop_reason=StopReason.tool_error,
        )

    latency_ms = (time.perf_counter() - start) * 1000

    intermediate_steps = result.get("intermediate_steps", [])
    trace: list[ThoughtStep] = []

    for i, (action, observation) in enumerate(intermediate_steps, start=1):
        thought_text = getattr(action, "log", "") or ""

        if "Action:" in thought_text:
            thought_text = thought_text.split("Action:")[0].strip()

        trace.append(
            ThoughtStep(
                step_number=i,
                thought=thought_text,
                tool=getattr(action, "tool", None),
                tool_input=str(getattr(action, "tool_input", "")),
                observation=str(observation),
            )
        )

    raw_output = result.get("output", "")

    if len(trace) >= request.max_iterations:
        stop_reason = StopReason.iteration_limit
        final_answer = (
            f"I could not reach a final answer within {request.max_iterations} steps. "
            f"Here is what I found so far: {raw_output}"
        )
    else:
        stop_reason = StopReason.final_answer
        final_answer = raw_output

    response = AgentResponse(
        final_answer=final_answer,
        trace=trace if request.return_trace else [],
        iterations=len(trace),
        latency_ms=latency_ms,
        stop_reason=stop_reason,
    )

    if request.session_id is not None:
        add_turn(
            session_id=request.session_id,
            query=request.query,
            answer=response.final_answer,
        )

    return response


@router.get("/history/{session_id}", response_model=AgentHistoryResponse)
def get_agent_history(session_id: str) -> AgentHistoryResponse:
    """Return completed turns stored for one conversation session."""

    turns = get_turns(session_id)

    if turns is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    return AgentHistoryResponse(
        session_id=session_id,
        turns=[
            ConversationTurnResponse(
                query=turn.query,
                answer=turn.answer,
                timestamp=turn.timestamp,
            )
            for turn in turns
        ],
    )