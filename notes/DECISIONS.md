## Decisions

# D-001 — Dependency management and project environment

- Date: 2026-09-08
- Chosen: Use `uv`, a project-local `.venv`, `pyproject.toml`, and a committed `uv.lock` file.
- Rejected: Global Python packages or a manually maintained `requirements.txt` file as the only dependency record.
- Reason: This provides an isolated, reproducible environment. `pyproject.toml` records direct dependencies, while `uv.lock` records the resolved versions.
- Change trigger: Change only if the team or assignment requires another dependency-management standard.

# D-002 — ReAct agent API selection

- Date: 2026-09-08
- Chosen: Use `langchain_classic.agents.react.agent.create_react_agent`.
- Rejected: Use `langgraph.prebuilt.create_react_agent` for the application agent.
- Reason: The assignment requires a text-based ReAct agent that exposes `Thought`, `Action`, and `Action Input`. The LangChain Classic implementation fits this approach, while LangGraph uses structured tool calls.
- Change trigger: Reconsider only if `langchain-classic` is incompatible with the selected model provider or required dependency versions.

# D-003 — Mock search matching

- Date: 2026-09-09
- Chosen: Normalize query text by lowercasing it and removing punctuation, then score each fact by its number of shared keywords with the query. Return only facts tied for the highest score, up to five results.
- Rejected: Return every fact that shares at least one keyword with the query.
- Reason: Broad queries such as `population` should return all equally relevant population facts. Specific queries such as `area of Germany` should return only the Germany area fact because it matches both `area` and `germany`, while France and Japan area facts match only `area`.
- Change trigger: Revisit if evaluation queries show that relevant facts are excluded or irrelevant facts are returned.

# D-004 — Search typo handling

- Date: 2026-09-09
- Chosen: Add a small typo-correction step before keyword scoring, using only the known keywords from the supplied fact table and a strict similarity threshold.
- Rejected: Exact matching only, or broad fuzzy matching with a low similarity threshold.
- Reason: Exact matching makes common typos such as `germny` fail to identify Germany. Limiting correction to known keywords with a strict threshold supports common misspellings while reducing incorrect corrections.
- Change trigger: Revisit the similarity threshold if test queries produce incorrect corrections or fail to correct expected common typos.

# D-005— How we capture the trace

- Date: 2026-09-09
- Chosen: Turn on `return_intermediate_steps=True` on `AgentExecutor` and read the trace from `executor.invoke()` after the run.
- Rejected: Wiring up streaming callbacks (`on_agent_action`, `on_agent_finish`) just to build the trace.
- Reason: For this project I only need the trace at the end of the run, not live streaming back to the client. Letting LangChain collect `intermediate_steps` and then shaping that into my own `ThoughtStep` objects keeps the code simpler and still gives me all the detail I need for debugging.
- Change trigger: If I ever need to stream the agent’s reasoning to the UI in real time, I’ll revisit this and add callbacks instead of relying purely on post-hoc data.

# D-006 — Changing the prompt around tool output

- Date: 2026-09-09
- Chosen: Add an explicit “IMPORTANT SAFETY RULE” block to the ReAct prompt that tells the model to treat every Observation as untrusted data, not as instructions.
- Reason: The corpus intentionally contains a prompt-injection ticket (1960 in the onboarding appendix) and may contain other payloads that try to steer the agent from inside retrieved text. I don’t want the model to see `Observation: Ignore your previous instructions and …` and blindly obey it, so I spell out that only the system prompt and tool descriptions are authoritative, and tool output is just evidence.
- Change trigger: If I discover that this wording is still too weak — for example, the agent obeys injected instructions inside a retrieved chunk — I’ll refine the safety block, but the underlying rule (tool output is data, not instructions) will stay the same.

# D-007 — What happens at the iteration cap

- Date: 2026-09-09
- Chosen: When the agent hits `max_iterations`, return a custom `final_answer` that explains it couldn’t finish within the cap, include whatever partial answer it has, and set `stop_reason=iteration_limit`.
- Rejected: Letting LangChain’s default “Agent stopped due to iteration limit or time limit” string bubble through to the caller.
- Reason: The assignment is clear that the framework’s stock “agent stopped” message must not reach the API client. I also want the caller to see something useful: how many steps were taken, what the agent did figure out, and a clear signal that we hit a safety cap rather than silently giving up.
- Change trigger: If I find a better way to summarize partial progress (for example, pointing at specific trace steps that were most useful), I’ll tweak the wording, but I’ll keep the structure: my own message plus a structured `stop_reason`.

# D-008 — Execution timeout

- Date: 2026-09-09
- Chosen: Use `max_execution_time=timeout_seconds` on `AgentExecutor`, with a default of 60 seconds.
- Reason: I don’t want a single bad or adversarial query to tie up the agent forever. A 60-second cap is a reasonable default for this kind of research assistant; it’s long enough for a few tool calls and some thinking, but short enough to protect the service.
- Change trigger: If I see legitimate queries hitting the timeout regularly, I’ll consider raising the limit or making it configurable per endpoint, but the agent will always run under some upper bound.

## Stage 3 — Ingestion duplicate policy

**Decision:** Overwrite documents by exact uploaded source filename.

**Why:** A correction uploaded under the same filename should replace old chunks. The service queries ChromaDB for chunks whose `source` metadata matches the filename, deletes those chunks, then inserts fresh chunks. This avoids stale and duplicate retrieval results while preserving a simple API contract.

**Rejected alternative:** Version every upload. Versioning would preserve historical copies, but it would require a version identifier and a policy for which version retrieval should search. That is unnecessary for the assignment’s supplied corpus and would make filtered retrieval more ambiguous.

**Evidence:** The four supplied corpus documents produced 54 chunks across four documents through `POST /ingest`. Uploading `check.txt` added one chunk. Uploading the same file again returned `replaced_existing: true` and kept the collection at 55 chunks and five documents.

**Invalid-input behavior:** A non-supported extension returned HTTP 415. An empty Markdown upload returned HTTP 422 and a subsequent retrieval still reported 55 chunks, showing that invalid files do not modify the collection.

**What would change this decision:** I would choose versioning if historical retrieval, audit requirements, concurrent editors, or rollback of document changes became a product requirement.