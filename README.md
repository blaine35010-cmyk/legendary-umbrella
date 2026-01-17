# Court AI Agent

A local-first AI agent for ingesting, indexing, and querying court case files. Uses SentenceTransformers for embeddings and cosine similarity search, with optional ChatGPT integration for generative responses.

## Features
- **Local-First**: No external APIs or data exfiltration—runs entirely on your machine.
- **Document Ingestion**: Extracts text from PDFs, DOCX, and images (OCR).
- **Vector Search**: Embeds documents and retrieves relevant chunks.
- **Generative QA**: Optional integration with OpenAI ChatGPT for natural language answers based on retrieved context.
- **Dynamic Updates**: Refresh data when files change via API endpoint.
- **Web UI**: Simple interface for queries with source citations.

## Setup
1. Clone the repo.
2. Install dependencies: `pip install -r requirements.txt` (or use venv).
3. Run locally: `python -m ingest.run_ingest && python -m index.chunk_and_embed`
4. Start web app: `uvicorn web.app:app --host 0.0.0.0 --port 8000`

## ChatGPT Integration (Optional)
To enable generative responses using OpenAI ChatGPT:
1. Get an OpenAI API key from https://platform.openai.com/api-keys.
2. Set the environment variable: `export OPENAI_API_KEY=your_key_here`
3. The agent will use ChatGPT for answers when the key is provided, falling back to retrieval-only if not.

## Docker Usage
- Pull image: `docker pull ghcr.io/blaine35010-cmyk/court-ai:latest`
- Run with volume mount: `docker run -d -p 8001:8000 -v "C:\path\to\court\files:/app/dropbox" -e CASE_ROOT="/app/dropbox" -e OPENAI_API_KEY=your_key ghcr.io/blaine35010-cmyk/court-ai:latest`
- Access UI: `http://localhost:8001`

## PowerShell Helpers
- Start: `.\start-court-ai.ps1 -ImageTag v1.3.1`
- Stop: `.\stop-court-ai.ps1`
- Smoke Test: `.\smoke-test.ps1 -ImageTag v1.3.1`

## API Endpoints
- `GET /health`: Health check.
- `POST /ask`: Query documents (JSON: {"question": "text", "format": "compact/detailed", "path_contains": "filter"}).
- `POST /update`: Re-ingest and re-index files (background task).

## Updating Data
- Add files to the mounted directory.
- Call `POST /update` to refresh embeddings.

## Requirements
- Python 3.10+
- Docker (optional)
- Court files in supported formats (PDF, DOCX, TXT, images).

## Security
- Data stays local; no network calls except for optional updates and ChatGPT API.
- Use volume mounts for file access.
- Keep API keys secure.
