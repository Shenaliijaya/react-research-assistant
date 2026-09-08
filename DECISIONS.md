# Decisions

## D-001 — Dependency management and project environment

- Date: 2026-09-08
- Chosen: Use `uv`, a project-local `.venv`, `pyproject.toml`, and a committed `uv.lock` file.
- Rejected: Global Python packages or a manually maintained `requirements.txt` file as the only dependency record.
- Reason: This provides an isolated, reproducible environment. `pyproject.toml` records the project dependencies, while `uv.lock` records the resolved package versions.
- Change trigger: Change only if the team or assignment requires another dependency-management standard.

## D-002 — ReAct agent API selection

- Date: 2026-09-08
- Chosen: Use `langchain_classic.agents.react.agent.create_react_agent`.
- Rejected: Use `langgraph.prebuilt.create_react_agent` for the application agent.
- Reason: The assignment requires a text-based ReAct agent using `Thought`, `Action`, and `Action Input`. The LangChain Classic implementation supports this format and makes tool-selection and parsing behavior easier to inspect during development. LangGraph uses structured tool calls instead, which does not match the required approach as closely.
- Change trigger: Reconsider only if `langchain-classic` is incompatible with the selected model provider or required dependency versions.