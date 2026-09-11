# ReAct Research Assistant API

A FastAPI-based Research Assistant Agent that answers questions using a text-parsed ReAct loop. The agent can search mock world facts, retrieve information from an ingested Tideline document corpus using ChromaDB, and perform safe arithmetic calculations.

The project was built as a staged junior-developer assignment. It includes document ingestion, retrieval-augmented generation session-based conversation memory, an evaluation harness, a ReAct-versus-single-shot-RAG comparison, API robustness tests, and prompt-injection testing.

## Features

- FastAPI REST API with Pydantic request and response models.
- Three agent tools:
  - `search` for mock general world facts.
  - `retrieve` for Tideline and Halcyon Labs document-corpus questions.
  - `calculate` for safe arithmetic expressions.
- Text-parsed LangChain ReAct agent using `Thought`, `Action`, `Action Input`,
  and `Observation` steps.
- ChromaDB-backed semantic retrieval with chunk source metadata.
- `POST /ingest` endpoint for Markdown and plain-text document ingestion.
- Exact-filename overwrite policy for duplicate document uploads.
- Session-based in-memory conversation history.
- `GET /agent/history/{session_id}` endpoint.
- `GET /health` endpoint that checks the live ChromaDB datastore.
- `GET /agent/info` endpoint that reports the live agent tool registry and
  configuration.
- Full Stage 4 evaluation harness with tool-path checks and saved traces.
- Endpoint fuzz testing for malformed and hostile input.
- Direct and indirect prompt-injection resistance checks.

## Architecture

```text
Client
  |
  v
FastAPI routes
  |
  +--> /tools/search ------> search service
  +--> /tools/retrieve ----> ChromaDB retrieval service
  +--> /tools/calculate ---> safe AST calculator service
  +--> /ingest ------------> chunking and ChromaDB storage
  +--> /agent/query -------> ReAct agent executor
                                  |
                                  +--> search / retrieve / calculate
                                  |
                                  v
                              AgentResponse with trace
```

The agent's three tools call plain Python service functions. This keeps tool logic independent from FastAPI and LangChain so that the same service functions can be called through HTTP routes and through the agent tool wrappers.

## Requirements

- Python 3.11 or newer.
- A Google Gemini API key.
- The project's pinned Python dependencies installed in a virtual environment.
- The four supplied corpus documents available in the project `corpus/` folder.

## Setup

### 1. Clone the repository

```bat
git clone <https://github.com/Shenaliijaya/react-research-assistant.git>
cd react-research-assistant
```

Replace `<YOUR_REPOSITORY_URL>` with your own GitHub repository URL.

### 2. Create and activate a virtual environment

Windows Command Prompt:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

Use the project's pinned dependency file:

```bat
pip install -r requirements.txt
```

If the project uses a lockfile, install dependencies using the lockfile command documented by the chosen package manager.

### 4. Configure environment variables

Create a `.env` file in the project root.

```env
GOOGLE_API_KEY=replace_with_your_google_gemini_api_key
LLM_MODEL=gemini-3.5-flash-lite
```

Do not commit `.env` to Git. Keep real API keys private.

## Run the API

From the project root, activate the virtual environment and run:

```bat
.venv\Scripts\activate.bat
uvicorn react_research_assistant.main:app --reload
```

Open the interactive API documentation in a browser:

```text
http://127.0.0.1:8000/docs
```

The server initializes or loads an empty ChromaDB collection at startup. The corpus must be ingested through the API before running corpus-based retrieval or agent evaluations.

## Ingest the corpus

Use `POST /ingest` in `/docs` to upload the four supplied Markdown files:

```text
corpus/01-tideline-pricing-faq.md
corpus/02-rfc-014-retention-and-downsampling.md
corpus/03-engineering-onboarding-guide.md
corpus/04-postmortem-inc-2291.md
```

The selected production configuration uses:

```text
Chunk size: 1500 characters
Chunk overlap: 150 characters
Expected collection: 30 chunks from 4 documents
```

Uploading an already-ingested filename replaces its existing stored chunks.
This avoids duplicate or stale chunks when a source file is re-uploaded.

Verify ingestion with:

```text
GET /health
```

A healthy collection after the four corpus uploads should report a collection size of 30.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/tools/search` | Search supplied mock world-fact data |
| POST | `/tools/retrieve` | Retrieve relevant ChromaDB corpus chunks |
| POST | `/tools/calculate` | Safely evaluate an arithmetic expression |
| POST | `/ingest` | Upload and ingest a `.md` or `.txt` document |
| POST | `/agent/query` | Run the ReAct research agent |
| GET | `/agent/history/{session_id}` | Retrieve saved session turns |
| GET | `/agent/info` | Show live tools, model, and agent limits |
| GET | `/health` | Check API and ChromaDB datastore health |

## Example requests

### 1. Retrieve a corpus fact

Request:

```json
POST /tools/retrieve
{
  "query": "What is Tideline's storage overage rate and is storage measured in GB or GiB?",
  "result_count": 3
}
```

Example result:

```json
{
  "results": [
    {
      "chunk_id": "01-tideline-pricing-faq-chunk-0",
      "source": "01-tideline-pricing-faq.md",
      "chunk_index": 0,
      "text": "Storage overage is billed at $0.09 per GB-month. Storage is measured in decimal GB (10^9 bytes), not GiB.",
      "distance": 0.0
    }
  ],
  "total_chunks": 30,
  "truncated": true
}
```

### 2. Perform a safe calculation

Request:

```json
POST /tools/calculate
{
  "expression": "68170000 / 357022"
}
```

Example result:

```json
{
  "expression": "68170000 / 357022",
  "result": 190.94061430388044
}
```

Unsafe expressions such as `__import__('os').system('dir')`, division by zero, and extremely large exponent values are rejected with clean client errors and do not execute code.

### 3. Run an agent query

Request:

```json
POST /agent/query
{
  "query": "A Team customer averages 340 GB of storage. What is their monthly storage overage charge, and does the annual prepay discount reduce it?",
  "session_id": null,
  "max_iterations": 10,
  "return_trace": true
}
```

Example result:

```json
{
  "final_answer": "A Team customer averaging 340 GB of storage has 240 GB of overage because 100 GB is included. At $0.09 per GB-month, the monthly storage overage charge is $21.60. The annual prepay discount does not reduce storage overage charges.",
  "iterations": 2,
  "stop_reason": "final_answer"
}
```

The trace for this request shows the expected tool path:

```text
retrieve -> calculate
```

## Conversation memory

Send related requests with the same `session_id`.

Example first request:

```json
POST /agent/query
{
  "query": "What does the onboarding guide say about setting up the dev environment?",
  "session_id": "demo-session",
  "return_trace": true
}
```

Example follow-up:

```json
POST /agent/query
{
  "query": "What about the testing section?",
  "session_id": "demo-session",
  "return_trace": true
}
```

The latest six completed turns are inserted into the ReAct prompt as formatted history. History is used to resolve references such as “the testing section” or “both,” but corpus claims still require retrieval.

The current store is in-memory. Sessions are cleared on restart and are not shared between multiple Uvicorn worker processes. A production implementation would use shared storage such as Redis or a database.

## Run the Stage 4 evaluation

Start the API first, then open a second terminal at the project root and run:

```bat
.venv\Scripts\activate.bat
python src\react_research_assistant\eval\runner.py
```

The harness runs the supplied question bank plus six custom questions. It
records:

- pass/fail;
- HTTP status;
- stop reason;
- expected and actual tool path;
- iteration count;
- latency;
- final answer;
- full trace;
- failure classification.

Saved evaluation files are placed in:

```text
src/react_research_assistant/eval/results/
```

## Run the agent comparison

The Stage 4 baseline comparison measures the normal ReAct agent against a single-shot RAG alternative on A1, B1, and C1.

Start the API, then run:

```bat
python src\react_research_assistant\eval\baseline_comparison.py
```

The script saves:

```text
src/react_research_assistant/eval/results/stage4_baseline_comparison.json
src/react_research_assistant/eval/results/stage4_baseline_comparison.md
```

In the recorded comparison run, both approaches scored 2/3. The ReAct agent had a median latency of 3700.1 ms and used two LLM calls per question.
Single-shot RAG had a median latency of 2382.8 ms and used one LLM call per question.

## Run robustness fuzzing

Start the API, then run:

```bat
python src\react_research_assistant\eval\fuzz_endpoints.py
```

The fuzz suite tests malformed JSON, missing fields, empty/whitespace-only queries, a 50,000-character query, Unicode input, invalid iteration limits, null sessions, invalid retrieval limits, and hostile calculator inputs.

Results are saved in:

```text
src/react_research_assistant/eval/results/stage4_fuzz_results.csv
src/react_research_assistant/eval/results/stage4_fuzz_results.json
```

The recorded Stage 4 fuzz run passed all 27 cases with zero HTTP 500-series errors.

## Prompt-injection handling

The corpus contains a deliberate prompt-injection payload in onboarding Ticket 1960. The ReAct prompt treats text returned by tools as untrusted observation data rather than instructions.

The system prompt explicitly instructs the model not to follow commands found inside observations, including text that attempts to override instructions.
The F1 direct-injection and F2 indirect-injection evaluation cases passed: the agent did not reveal its system prompt and described Ticket 1960 as an injection attempt rather than obeying its content.

## Known limitations

- The text-parsed ReAct loop can produce parser exceptions when model output does not follow the required `Thought`, `Action`, and `Action Input` format.
- Complex multi-step calculations are less reliable than simple retrieval or retrieval-plus-calculation questions. D1 reached the iteration cap in repeated evaluation runs.
- The agent sometimes repeats retrieval unnecessarily, increasing latency and risking the configured 60-second execution limit.
- The current session store is process-local and in-memory.
- The single-shot RAG comparison showed that an agent loop is overhead for simple document lookups where one retrieval and one model answer are enough.

## Project evidence

Stage 4 outputs are retained under:

```text
src/react_research_assistant/eval/results/
```

They include:

- baseline and follow-up evaluation results;
- detailed traces;
- evaluation analysis;
- ReAct versus single-shot RAG comparison;
- fuzz-test CSV and JSON results;
- robustness analysis.
