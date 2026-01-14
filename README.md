# court_ai_agent — ingestion

This workspace contains ingestion tools to scan a local Dropbox case folder and extract raw text + metadata into JSON files.

Quick setup

1. (Optional but recommended) Create a Python virtualenv and activate it.

2. Install Python requirements for OCR and PDF support:

```bash
pip install -r requirements.txt
# On Windows also install poppler and Tesseract and add them to PATH
```

Run the scanner (lists files):

```bash
python ingest/scan_files.py
```

Dry-run the ingestion (list only):

```bash
python -m ingest.run_ingest --dry-run
```

Run full ingestion (may require dependencies):

```bash
python -m ingest.run_ingest
```

Extracted JSON files are written to `data/raw_docs/`.

Local indexing and QA

- Index a sample of documents (50) into the local store:

```bash
python -m index.chunk_and_embed_chroma --json-dir data/raw_docs --collection court-files --sample 50
```

- Index the entire corpus:

```bash
python -m index.chunk_and_embed_chroma --json-dir data/raw_docs --collection court-files
```

- Run local QA using the numpy-backed store (no API keys required):

```bash
python -m agent.ask --question "When was the Final Trial Preparation Summary dated?"
```

Cloud mode (optional):

- To use OpenAI + Pinecone for higher-quality embeddings and managed vector DB, set these environment variables:

```
OPENAI_API_KEY=...
PINECONE_API_KEY=...
PINECONE_ENV=...
```

- When keys are present, `agent.ask` will automatically prefer the cloud path.

`agent.ask` supports two local output formats when OpenAI is not configured:

- `--format compact` (default): concise 2-4 sentence summary with numbered source citations.
- `--format detailed`: short extracted snippets with metadata for quick inspection.

Example (detailed):

```bash
python -m agent.ask --question "Summarize the Final Trial Preparation Summary." --format detailed
```

Web UI

Start a small local API server (FastAPI + Uvicorn):

```bash
python -m pip install fastapi uvicorn
uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Then POST to `/ask`:

```bash
curl -X POST "http://127.0.0.1:8000/ask" -H "Content-Type: application/json" -d '{"question":"Summarize the Final Trial Preparation Summary.","format":"compact"}'
```

Browser UI
----------

Start the FastAPI server and open the simple web UI at `http://127.0.0.1:8000/`:

```bash
uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Docker
------

Build and run the app in Docker:

```bash
docker build -t court-ai .
# Run the container locally with an automatic restart policy:
docker run --rm -d --restart unless-stopped -p 8000:8000 --name court-ai-run court-ai

# Stop and remove the container (if needed):
docker rm -f court-ai-run
```

Quick server helpers (Windows)
------------------------------

Start the server from the repo root (PowerShell):

```powershell
.\run_server.ps1
```

Or from cmd:

```cmd
run_server.bat
```

Docker Compose
--------------

Start with compose:

```bash
docker-compose up --build
```

Filtering precedence
-------------------

When using `--date-from`, `--date-to`, `--path-contains`, or `--file-ext`, the agent applies filters in this order:

- Filesystem modification time (`os.path.getmtime(file_path)`) when the original file path is present and accessible.
- Metadata returned by the vector store (fields such as `modified_time`, `mtime`, or `file_mtime`).
- Fallback to the raw JSON extracted at `data/raw_docs/{doc_id}.json` (fields like `modified_time`, `mtime`, or `modified`).

This ensures filters still work even if the original files have been moved or the environment cannot access them directly.
