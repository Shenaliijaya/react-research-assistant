import time
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv

from react_research_assistant.agent.factory import build_agent_executor
from react_research_assistant.services.retrieval import initialize_retrieval

load_dotenv()
initialize_retrieval()


@dataclass
class EvalQuestion:
    id: str
    prompt: str
    tools_expected: List[str]


@dataclass
class EvalResult:
    id: str
    passed: bool
    stop_reason: str
    tools_expected: List[str]
    tools_called: List[str]
    iterations: int
    latency_ms: float
    final_answer: str


def run_question(q: EvalQuestion) -> EvalResult:
    executor = build_agent_executor(max_iterations=10, timeout_seconds=60)

    start = time.perf_counter()
    result = executor.invoke({"input": q.prompt})
    latency_ms = (time.perf_counter() - start) * 1000

    intermediate_steps = result.get("intermediate_steps", [])
    tools_called = [getattr(action, "tool", None) for action, _ in intermediate_steps]
    stop_reason = "iteration_limit" if len(intermediate_steps) >= 10 else "final_answer"
    final_answer = result.get("output", "")

    if q.id == "A2":
        text = final_answer.lower()
        passed = ("30" in text and "day" in text) and ("read-only" in text or "export" in text)
    elif q.id == "D5":
        text = final_answer.lower()
        passed = ("does not" in text or "not stated" in text or "don't know" in text or "no information" in text) and "2,400" not in final_answer and "2400" not in final_answer
    else:
        passed = False

    return EvalResult(
        id=q.id,
        passed=passed,
        stop_reason=stop_reason,
        tools_expected=q.tools_expected,
        tools_called=tools_called,
        iterations=len(intermediate_steps),
        latency_ms=latency_ms,
        final_answer=final_answer,
    )


def run_eval() -> List[EvalResult]:
    questions = [
        EvalQuestion(
            id="A2",
            prompt="How long does a customer have to export their data after cancelling?",
            tools_expected=["retrieve"],
        ),
        EvalQuestion(
            id="D5_lightyear",
            prompt="What is a light-year in kilometres?",
            tools_expected=["search", "search", "calculate"],
        ),
        EvalQuestion(
            id="D5",
            prompt="How many paying customers does Halcyon Labs have?",
            tools_expected=["retrieve"],
        ),
    ]

    results: List[EvalResult] = []
    for q in questions:
        r = run_question(q)
        results.append(r)
        print(
            f"{r.id} | passed={r.passed} | stop_reason={r.stop_reason} | "
            f"tools_expected={r.tools_expected} | tools_called={r.tools_called} | "
            f"iterations={r.iterations} | latency_ms={r.latency_ms:.1f}\n"
            f"  final_answer: {r.final_answer[:200]}\n"
        )

    return results


if __name__ == "__main__":
    run_eval()