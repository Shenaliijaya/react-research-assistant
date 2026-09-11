# Stage 3 memory checks

Date: 2026-09-11

## History endpoint

I checked an unknown session first:

```text
GET /agent/history/not-a-real-session
```

It returned HTTP 404:

```json
{
  "detail": "Session not found."
}
```

Then I sent an agent request using a session ID and called the history endpoint for that same ID. The response contained the session ID and one stored turn with the original query, final answer, and timestamp.

## G1 conversation test

I used `g1-demo` for all three turns.

### Turn 1

```text
What does the onboarding guide say about setting up the dev environment?
```

The agent retrieved the onboarding guide and answered about development environment setup.

### Turn 2

```text
What about the testing section?
```

The first retrieval input was:

```text
onboarding guide testing section
```

The words `onboarding guide` are not in Turn 2 itself. They came from the previous turn, so this showed that the session history was reaching the prompt and helping the agent resolve the follow-up.

### Turn 3

```text
Put both in a table.
```

The retrieval input was:

```text
onboarding guide dev environment and testing
```

The answer returned one table covering both development setup and testing. The agent understood `both` as the two earlier subjects.

## Fresh session check

I sent this in a new session called `fresh-session-g1`:

```text
What about the testing section?
```

The retrieval input was:

```text
testing section Halcyon Labs Tideline
```

It did not include `onboarding guide`, unlike Turn 2 in `g1-demo`. This shows the new session did not receive the previous session's conversation history.

The fresh query still retrieved some onboarding-guide content. That is okay because it was a new semantic search result, not stored context from `g1-demo`.

## Current limitation

The session store is an in-memory dictionary.

- It works across separate requests while this FastAPI process is running.
- Restarting the API clears sessions.
- More than one Uvicorn worker would have separate session dictionaries.
- A production version would use shared storage such as Redis or a database.

I currently send the last six completed turns into the prompt. This prevents history from growing without a limit while still covering short follow-up conversations like G1.