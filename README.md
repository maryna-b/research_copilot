# Research Copilot

> A personal AI research assistant that ingests PDF papers, indexes them semantically, and lets you search across them with natural language.

---

## What It Does

- **Upload** PDFs → automatic text extraction and chunking
- **Search** across all uploaded papers with semantic (meaning-based) search
- **Relevance scores** on every result so you can gauge match quality at a glance

---

## Architecture

Single FastAPI app backed by PostgreSQL (metadata) and Chroma (vector embeddings).

```
Client → app (8000)
           ├── PostgreSQL (5432) — document metadata
           └── Chroma (8002)    — vector embeddings
```

**Stack:** FastAPI · PostgreSQL · SQLAlchemy · Chroma · OpenAI embeddings · pdfplumber · Prometheus

---

## Quick Start

### With Docker Compose (recommended)

```bash
cp .env.example .env   # fill in OPENAI_API_KEY and Postgres credentials
docker-compose up --build
```

App available at: http://localhost:8000/docs

### Local (no Docker for the app)

PostgreSQL and Chroma still need Docker:

```bash
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=research_user \
  -e POSTGRES_PASSWORD=research_pass \
  -e POSTGRES_DB=research_copilot \
  postgres:15-alpine

docker run -d -p 8002:8000 chromadb/chroma:0.5.23
```

Then run the app:

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd app && uvicorn main:app --reload --port 8000
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `API_KEY` | `dev-key-change-in-production` | Authentication key for protected endpoints |
| `DATABASE_URL` | `sqlite:///./documents.db` | PostgreSQL connection string |
| `OPENAI_API_KEY` | — | Required for embeddings |
| `CHROMA_HOST` | `localhost` | Chroma server host |
| `CHROMA_PORT` | `8000` | Chroma server port |
| `MAX_FILE_SIZE` | `52428800` (50MB) | Upload size limit in bytes |
| `CHUNK_SIZE` | `1000` | Characters per text chunk |
| `CHUNK_OVERLAP` | `100` | Overlap between chunks |

---

## API Endpoints

### Public (no auth)
| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/docs` | Interactive API docs |

### Protected (`X-API-Key` header required)
| Method | Path | Description |
|---|---|---|
| `POST` | `/upload` | Upload and index a PDF |
| `POST` | `/search` | Semantic search across documents |
| `GET` | `/documents` | List all uploaded documents |
| `GET` | `/info` | App version info |

### Example usage

```bash
# Upload a PDF
curl -X POST http://localhost:8000/upload \
  -H "X-API-Key: dev-key-change-in-production" \
  -F "file=@paper.pdf"

# Search
curl -X POST http://localhost:8000/search \
  -H "X-API-Key: dev-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer attention mechanism", "n_results": 5}'

# List documents
curl http://localhost:8000/documents \
  -H "X-API-Key: dev-key-change-in-production"
```

---

## Testing

```bash
venv/bin/pytest tests/ -v

# With coverage
venv/bin/pytest tests/ --cov=app --cov-report=html
```

---

## Logs & Monitoring

```bash
# Docker logs
docker-compose logs -f app

# Prometheus metrics
curl http://localhost:8000/metrics
```

Every request gets a unique `X-Request-ID` header for tracing across logs.

---

## Project Structure

```
app/
├── main.py        # FastAPI app and all routes
├── auth.py        # API key middleware
├── config.py      # Settings from environment variables
├── database.py    # SQLAlchemy engine and session
├── models.py      # Document ORM model
├── schemas.py     # Pydantic request/response schemas
├── ingestion.py   # PDF extraction and chunking logic
├── embeddings.py  # OpenAI embeddings and Chroma search
├── utils.py       # chunk_text utility
└── Dockerfile
tests/
docker-compose.yml
requirements.txt
```

---

## Roadmap

### Done
- [x] PDF upload, text extraction, sentence-boundary aware chunking
- [x] OpenAI vector embeddings stored in Chroma
- [x] Semantic search with relevance scores
- [x] API key auth, structured logging, Prometheus metrics

### Next
- [ ] `/ask` endpoint — RAG question answering with citations
- [ ] LangGraph multi-agent workflows
- [ ] Web UI
