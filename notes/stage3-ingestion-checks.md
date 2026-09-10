# Stage 3 Ingestion Checks

Date: 2026-09-10

## Fresh collection check

I stopped the API, deleted the local `chroma_db` directory, and restarted the application.

Before uploading any document, I called `POST /tools/retrieve` with a normal query. The response returned an empty `results` list and:

```json
{
  "total_chunks": 0,
  "truncated": false
}
```

This verified that the application startup lifecycle creates or loads the ChromaDB collection but does not automatically seed the supplied corpus. The corpus is now loaded through `POST /ingest`.

## Initial corpus ingestion

I uploaded all four supplied corpus documents through `POST /ingest`.

| Source file | Chunk count | Total chunks after upload | Total documents | Replaced existing |

| `01-tideline-pricing-faq.md` | 11 | 11 | 1 | false |
| `02-rfc-014-retention-and-downsampling.md` | 14 | 25 | 2 | false |
| `03-engineering-onboarding-guide.md` | 15 | 40 | 3 | false |
| `04-postmortem-inc-2291.md` | 14 | 54 | 4 | false |

The chunk counts add up to 54:

\[11 + 14 + 15 + 14 = 54\]

This confirms that all four supplied source documents entered the persistent collection through the ingestion API.

## Stored metadata

Each stored chunk includes this metadata:

- `source`: original uploaded filename
- `document_id`: stable identifier derived from the filename
- `chunk_index`: zero-based position of the chunk within its document
- `ingested_at`: UTC ISO 8601 timestamp created once per upload operation

The current service uses the `source` metadata value as the source filename required by the specification.

## Plain-text ingestion and retrieval

I created and uploaded a plain-text file named `check.txt` containing:

```text check document. The unique verification phrase is: violet lighthouse 742.
```

The first `POST /ingest` upload succeeded and added one chunk. I then queried `POST /tools/retrieve` with:

```json
{
  "query": "violet lighthouse 742",
  "result_count": 3
}
```

The top result was the uploaded file:

```json
{
  "chunk_id": "check-chunk-0",
  "source": "check.txt",
  "chunk_index": 0,
  "text": "Lunch check document. The unique verification phrase is: violet lighthouse 742.",
  "distance": 0.7280663251876831
}
```

The same search also returned two lower-ranked chunks from the supplied corpus because vector search returns the requested top \(k\) nearest chunks even when only one result is strongly relevant. The correct `check.txt` result had the lowest distance. The response reported `total_chunks: 55` and `truncated: true`.

This test showed that a text file uploaded through the API is stored, persists in ChromaDB, and can be retrieved using its content.

## Duplicate-upload policy

Policy: overwrite by exact source filename.

When a file is uploaded, the service searches for existing chunks whose `source` metadata exactly equals the uploaded filename. If it finds any, it deletes those chunks before storing newly created chunks from the uploaded text.

This avoids stale and duplicate chunks if a user corrects a document and uploads it again under the same name.

I uploaded `check.txt` a second time. The response was:

```json
{
  "document_id": "check",
  "source_filename": "check.txt",
  "chunk_count": 1,
  "total_chunks": 55,
  "total_documents": 5,
  "replaced_existing": true
}
```

The collection remained at five source documents and 55 chunks. It did not become 56 chunks, confirming that the second upload replaced the old chunk instead of duplicating it.

## Invalid-upload checks

### Unsupported extension

Uploading a file whose name did not end in `.md` or `.txt` returned:

```text
HTTP 415 Unsupported Media Type
```

```json
{
  "detail": "Only Markdown (.md) and plain-text (.txt) files are supported."
}
```

### Empty Markdown file

Uploading an empty file named `empty.md` returned:

```text
HTTP 422 Unprocessable Entity
```

```json
{
  "detail": "Document content cannot be empty."
}
```

I then called `POST /tools/retrieve` with:

```json
{
  "query": "retention",
  "result_count": 1
}
```

The response still reported:

```json
{
  "total_chunks": 55
}
```

This confirms that empty uploads are rejected without a server error and do not write data to ChromaDB.

## Current collection caveat

The temporary `check.txt` document is currently present in the local ChromaDB collection. Before running the official evaluation or testing the supplied question bank, I will reset the local vector database and re-ingest only the four supplied corpus documents. The final evaluation collection should contain 54 chunks from four supplied documents.