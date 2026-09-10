from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class ConversationTurn:
    """One completed user query and agent answer in a conversation session."""

    query: str
    answer: str
    timestamp: datetime


_sessions: dict[str, list[ConversationTurn]] = {}


def add_turn(session_id: str, query: str, answer: str) -> None:
    """Append one completed conversation turn to an in-memory session."""

    _sessions.setdefault(session_id, []).append(
        ConversationTurn(
            query=query,
            answer=answer,
            timestamp=datetime.now(UTC),
        )
    )


def get_turns(session_id: str) -> list[ConversationTurn] | None:
    """Return a copy of one session's turns, or None when it does not exist."""

    turns = _sessions.get(session_id)

    if turns is None:
        return None

    return list(turns)


def format_recent_history(session_id: str, max_turns: int = 6) -> str:
    """Format recent completed turns for insertion into the agent prompt."""

    turns = _sessions.get(session_id, [])[-max_turns:]

    if not turns:
        return "No previous conversation turns."

    return "\n\n".join(
        (
            f"Previous user question: {turn.query}\n"
            f"Previous assistant answer: {turn.answer}"
        )
        for turn in turns
    )