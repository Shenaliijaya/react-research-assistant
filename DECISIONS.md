# Decisions

## D-001 — Dependency management and project environment

- Date: 2026-09-08
- Chosen: Use `uv`, a project-local `.venv`, `pyproject.toml`, and a committed `uv.lock` file.
- Rejected: Global Python packages or a manually maintained `requirements.txt` file as the only dependency record.
- Reason: This provides an isolated, reproducible environment. `pyproject.toml` records direct dependencies, while `uv.lock` records the resolved versions.
- Change trigger: Change only if the team or assignment requires another dependency-management standard.

## D-002 — ReAct agent API selection

- Date: 2026-09-08
- Chosen: Use `langchain_classic.agents.react.agent.create_react_agent`.
- Rejected: Use `langgraph.prebuilt.create_react_agent` for the application agent.
- Reason: The assignment requires a text-based ReAct agent that exposes `Thought`, `Action`, and `Action Input`. The LangChain Classic implementation fits this approach, while LangGraph uses structured tool calls.
- Change trigger: Reconsider only if `langchain-classic` is incompatible with the selected model provider or required dependency versions.

## D-003 — Mock search matching

- Date: 2026-09-09
- Chosen: Normalize query text by lowercasing it and removing punctuation, then score each fact by its number of shared keywords with the query. Return only facts tied for the highest score, up to five results.
- Rejected: Return every fact that shares at least one keyword with the query.
- Reason: Broad queries such as `population` should return all equally relevant population facts. Specific queries such as `area of Germany` should return only the Germany area fact because it matches both `area` and `germany`, while France and Japan area facts match only `area`.
- Change trigger: Revisit if evaluation queries show that relevant facts are excluded or irrelevant facts are returned.

## D-004 — Search typo handling

- Date: 2026-09-09
- Chosen: Add a small typo-correction step before keyword scoring, using only the known keywords from the supplied fact table and a strict similarity threshold.
- Rejected: Exact matching only, or broad fuzzy matching with a low similarity threshold.
- Reason: Exact matching makes common typos such as `germny` fail to identify Germany. Limiting correction to known keywords with a strict threshold supports common misspellings while reducing incorrect corrections.
- Change trigger: Revisit the similarity threshold if test queries produce incorrect corrections or fail to correct expected common typos.