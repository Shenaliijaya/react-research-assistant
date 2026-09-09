# Stage 2 — Paper Trace

# Trace 1

Question: What is the population of France divided by the area of Germany in square kilometres?

Thought: I need the population of France. This is a general world fact, so I should use search.
Action: search
Action Input: population of France
Observation: The population of France is approximately 68,170,000 (2024 estimate). (source: mock://worldfacts/france)

Thought: Now I need the area of Germany, also a general world fact.
Action: search
Action Input: area of Germany
Observation: Germany has a total area of 357,022 square kilometres. (source: mock://worldfacts/germany)[file:7]

Thought: I have both numbers. Now I divide population of France by area of Germany.
Action: calculate
Action Input: 68170000 / 357022
Observation: 191.0068...

Thought: I now know the final answer.
Final Answer: The population of France divided by the area of Germany is approximately 191.01 people per square kilometre.

# Trace 2

Question: What is Tideline's backfill window for late writes?

Thought: This is a Tideline-specific technical question about how writes are handled, so I should use retrieve, not search.
Action: retrieve
Action Input: backfill window 48 hours late writes
Observation: RFC-014 states that the backfill window is 48 hours. Writes with a timestamp older than 48 hours are rejected with HTTP 409 Conflict (`backfill_window_exceeded`), and this limit is a hard constraint with no operator override or support bypass. (source: 02-rfc-014-retention-and-downsampling.md)[file:2]

Thought: I now know the final answer.
Final Answer: Tideline's backfill window for late writes is 48 hours, and writes older than that are rejected with HTTP 409.

# Trace 3

Question: What is the Team plan's default retention according to the pricing FAQ versus RFC-014?

Thought: This is about what customers are told versus what the system actually does, so I need to retrieve from both the pricing FAQ and RFC-014.
Action: retrieve
Action Input: Team plan default retention
Observation: The pricing FAQ (v4.2, reviewed 2026-02-14) says the Team plan has a 30-day retention window. RFC-014 (accepted 2026-04-11) says that effective 2026-05-01 the default advertised retention for new Team projects is 90 days, and notes the FAQ had not been updated yet. Projects created before 2026-05-01 keep 30 days until migrated. (sources: 01-tideline-pricing-faq.md, 02-rfc-014-retention-and-downsampling.md)[file:2][file:6]

Thought: I now know the final answer.
Final Answer: The pricing FAQ still says 30 days for Team, but RFC-014 changed the real default to 90 days for new Team projects from 2026-05-01 onwards. The disagreement is deliberate: the FAQ lags what the system does, and existing Team projects stay on 30 days until migration.

# Written Answers

1. By iteration 3, the model sees the entire scratchpad every time: the original question plus all prior Thought / Action / Action Input / Observation blocks glued together into one big text chunk. That means Observation 1 is not “used once and forgotten” — it’s resent in full on every subsequent call. If the loop runs 3 iterations total, Observation 1’s text is sent 3 times: once when it’s created, then twice more as part of the accumulated context on later iterations.

2. Token cost grows fastest in the scratchpad, not in the tools. Each new iteration only adds a bit of fresh text, but then the entire scratchpad is resent on the next LLM call. As the number of iterations goes up, you’re repeatedly sending more and more text, so the total tokens used across the whole run grow roughly with the square of the iteration count, even though each step only appends a small amount.

3. If the model writes `Action: calculator` but the registered tool is called `calculate`, LangChain’s `AgentExecutor` does a straight string match against the tool names. It doesn’t find `calculator`, so instead of throwing a 500 it treats this as a bad tool choice and returns an error string as the Observation, e.g. “calculator is not a valid tool, try one of [search, retrieve, calculate]”. That error then shows up as an Observation in the trace for that step, and the model gets another turn to fix the tool name on the next iteration.

4. If the model emits both a `Final Answer:` and an `Action:` in the same output, the classic ReAct output parser prioritises `Final Answer:`. Once it sees that marker, it treats the output as a finished answer (`AgentFinish`) and ignores everything after it, including any `Action:` line. In practice the loop ends on that step with the final answer, and the trailing Action is never executed.

# Parse failure observed

I hit a real validation / parsing failure while wiring up the search tool. At that point, the `SearchResult` model said `id` should be a string, but the loader was passing an integer index from the fact table (`1`, `2`, …). Pydantic refused to construct the model and surfaced this error:
