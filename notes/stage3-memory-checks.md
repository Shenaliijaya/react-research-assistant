# Stage 3 Session Memory Checks

Date: 2026-09-11

## History endpoint

- `GET /agent/history/not-a-real-session` returned HTTP 404 with:
  ```json
  {
    "detail": "Session not found."
  }
  ```
- A completed `POST /agent/query` request with a session ID created a stored turn.
- `GET /agent/history/{session_id}` returned the session ID and ordered turns containing the original query, final answer, and UTC timestamp.

## G1 conversation test

Session ID: `g1-demo`

### Turn 1

Query:

```text
What does the onboarding guide say about setting up the dev environment?
```

The agent retrieved the onboarding guide and returned development-environment information.

### Turn 2

Query:

```text
What about the testing section?
```

The first retrieval tool input was:

```text
onboarding guide testing section
```

This is the important trace evidence: the current message did not contain the words “onboarding guide,” so the agent could only produce that retrieval query because bounded conversation history was included in the prompt. The answer summarized the flaky-test policy and testing guidance from the onboarding guide.

### Turn 3

Query:

```text
Put both in a table.
```

The retrieval tool input was:

```text
onboarding guide dev environment and testing
```

The final answer returned a single table containing both development-environment and testing-section information. This showed that the agent resolved “both” to the subjects established in the two previous turns.

## Fresh-session isolation

Fresh session ID: `fresh-session-g1`

Query:

```text
What about the testing section?
```

The retrieval tool input was:

```text
testing section Halcyon Labs Tideline
```

It did not include `onboarding guide`, unlike Turn 2 in `g1-demo`. This indicates the new session did not receive the earlier session's context. It still found an onboarding-guide chunk through semantic retrieval, which is permitted; the important property is that the answer was not based on memory leaked from `g1-demo`.

## Storage and history limitation

The current session store is an in-memory Python dictionary.

- It persists across separate HTTP requests served by the same running application process.
- It does not survive an application restart.
- It is not shared across multiple Uvicorn worker processes.
- A production deployment would use shared persistent storage such as Redis or a database.

The prompt receives at most the most recent six completed turns. This bounds context growth while retaining enough local conversational context for short follow-up questions such as G1.