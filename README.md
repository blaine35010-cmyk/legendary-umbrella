# Court AI Agent

A local-first AI agent for ingesting, indexing, and querying court case files. Uses SentenceTransformers for embeddings and cosine similarity search, with a FastAPI web UI.

## Features
- **Local-First**: No external APIs or data exfiltration—runs entirely on your machine.
- **Document Ingestion**: Extracts text from PDFs, DOCX, and images (OCR).
- **Vector Search**: Embeds documents and retrieves relevant chunks.
- **Dynamic Updates**: Refresh data when files change via API endpoint.
- **Web UI**: Simple interface for queries with source citations.

## Setup
1. Clone the repo.
2. Install dependencies: `pip install -r requirements.txt` (or use venv).
3. Run locally: `python -m ingest.run_ingest && python -m index.chunk_and_embed`
4. Start web app: `uvicorn web.app:app --host 0.0.0.0 --port 8000`

## Docker Usage
- Pull image: `docker pull ghcr.io/blaine35010-cmyk/court-ai:latest`
- Run with volume mount: `docker run -d -p 8001:8000 -v "C:\path\to\court\files:/app/dropbox" -e CASE_ROOT="/app/dropbox" ghcr.io/blaine35010-cmyk/court-ai:latest`
- Access UI: `http://localhost:8001`

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
- Data stays local; no network calls except for optional updates.
- Use volume mounts for file access.
