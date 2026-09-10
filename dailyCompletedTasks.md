## Progress

# 2026-09-08

- Set up the Python project with `uv`, a local `.venv`, pinned dependencies, and `uv.lock`.
- Added `.gitignore` and created the initial project/package structure.
- Added initial Pydantic schemas for the search tool:
  - `SearchRequest`
  - `SearchResult`
  - `SearchResponse`
- Added validation for empty and whitespace-only search queries.
- Implemented initial search-tool logic that reads and matches the supplied `data/search-facts.md` table.
- Added the initial `POST /tools/search` FastAPI route.
- Started testing through FastAPI Swagger UI (`/docs`), but it currently shows “Failed to load API definition”; diagnosis is pending.

# 2026-09-09

- Fixed Swagger so `/docs` loads and shows all tool routes.
- Finished the mock search tool and confirmed `/tools/search` returns the expected facts.
- Implemented corpus retrieval with ChromaDB and added `/tools/retrieve`.
- Wired up the calculator tool and verified division-by-zero returns a clean error (no 500).
- Built the ReAct agent:
  - Registered `search`, `retrieve`, and `calculate` as tools.
  - Added `POST /agent/query` and confirmed it works for both world-fact and Tideline questions.
- Wrote `stage2-trace.md` and updated `DECISIONS.md` with Stage 2 choices.
- Started a minimal eval harness script to run a few of the provided questions against the agent.

# 2026-09-10

- Added document ingestion through `POST /ingest`.
  - Accepts UTF-8 Markdown (`.md`) and plain-text (`.txt`) uploads.
  - Rejects unsupported file extensions with HTTP 415.
  - Rejects empty uploads with HTTP 422 instead of returning a 500.
  - Added `python-multipart` as the FastAPI multipart upload dependency and updated `uv.lock`.

- Updated ChromaDB initialization.
  - The collection is created or loaded once at FastAPI startup.
  - Removed automatic corpus seeding at startup.
  - Confirmed that a fresh collection returns zero retrieval results before API uploads.

- Ingested all four supplied corpus documents through the API.
  - Stored 54 chunks across 4 documents after ingestion.
  - Verified duplicate upload replacement and successful plain-text retrieval.