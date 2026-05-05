# Research Copilot

> A personal AI research assistant that ingests documents, indexes them semantically, and performs intelligent search, summarization, and question-answering.

---

## What Does It Do?

Transform how you interact with research papers:

- **Upload** PDFs or documents → automatic text extraction and indexing
- **Search** semantic search (meaning-based, not just keywords)
- **Ask questions** → get AI-generated answers with exact citations and page references
- **Summarize** papers with structured notes (methods, results, limitations)
- **Compare** multiple papers side-by-side
- **Track** sources and verify factuality

---

## Current Features 

### Document Processing
- ✅ PDF upload via authenticated API
- ✅ Text extraction with pdfplumber
- ✅ Sentence-boundary aware text chunking
- ✅ Metadata storage in PostgreSQL

### Search & Embeddings
- ✅ Vector embeddings via OpenAI `text-embedding-3-small`
- ✅ Semantic search with Chroma vector database
- ✅ Relevance scores (0–1) alongside raw distances in search results

### Infrastructure
- ✅ API key authentication
- ✅ Structured logging with request IDs
- ✅ Prometheus metrics and monitoring
- ✅ Comprehensive error handling
- ✅ Input validation
- ✅ Docker containerization

### Coming Soon 
- 🚧 `/ask` question-answering endpoint (RAG)
- 🚧 Source citations and page references
- 🚧 Multi-agent workflows (LangGraph)

---

## Architecture

```
Client → API Gateway (8000) ┬→ Ingestion Service (8001) → PostgreSQL (5432)
                            │          ↓
                            │  Embeddings Service (8003)
                            │          ↓
                            └→ Chroma (8002)
```

**Services:**
- **API Gateway** (Port 8000) - Routing, authentication, logging, metrics
- **Ingestion Service** (Port 8001) - PDF processing, chunking, metadata storage
- **Embeddings Service** (Port 8003) - OpenAI embeddings, semantic search
- **PostgreSQL** (Port 5432) - Document metadata
- **Chroma** (Port 8002) - Vector embeddings store

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ 

### Run with Docker Compose

```bash
# Start all services
docker-compose up --build
```

**Services available at:**
- API Gateway: http://localhost:8000/docs
- Ingestion Service: http://localhost:8001/docs
- Metrics: http://localhost:8000/metrics

### Test the API

**Health check (public):**
```bash
curl http://localhost:8000/health
```

**Upload document (protected):**
```bash
curl -X POST http://localhost:8000/upload \
  -H "X-API-Key: dev-key-change-in-production" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "document_id": "uuid-here",
  "filename": "document.pdf",
  "total_chunks": 15,
  "chunks": [...]
}
```

---

## API Endpoints

### Public (No Auth)
- `GET /health` - Service health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - Interactive API documentation

### Protected (API Key Required)
- `POST /upload` - Upload and process PDF
- `POST /search` - Semantic search across indexed documents
- `GET /info` - Service information

**Authentication:** Include header `X-API-Key: key`

## Tech Stack

- **FastAPI** - Async web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM
- **pdfplumber** - PDF text extraction
- **Chroma** - Vector database
- **OpenAI** - Text embeddings (`text-embedding-3-small`)
- **Prometheus** - Metrics
- **Docker Compose** - Container orchestration

### Planned
- **LangChain / LangGraph** - LLM orchestration and multi-agent workflows
- **OpenAI GPT-4** - Question answering

---

## Local Development (No Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in your env vars (OPENAI_API_KEY is required)
cp .env.example .env
```

Start the infrastructure (PostgreSQL + Chroma still need Docker):

```bash
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=research_user \
  -e POSTGRES_PASSWORD=research_pass \
  -e POSTGRES_DB=research_db \
  postgres:15-alpine

docker run -d -p 8002:8000 chromadb/chroma
```

Then start each service in a separate terminal:

```bash
# Terminal 1 — Ingestion Service
cd services/ingestion_service && fastapi dev main.py --port 8001

# Terminal 2 — Embeddings Service
cd services/embeddings_service && fastapi dev main.py --port 8003

# Terminal 3 — API Gateway
cd services/api_gateway && fastapi dev main.py --port 8000
```

**Services available at:**
- API Gateway + docs: http://localhost:8000/docs
- Ingestion Service: http://localhost:8001/docs
- Embeddings Service: http://localhost:8003/docs

---

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=services --cov-report=html
```

---

## Monitoring

### Prometheus Metrics

- API Gateway: http://localhost:8000/metrics
- Ingestion Service: http://localhost:8001/metrics

### Logs

```bash
# View logs
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway
```
---

## Troubleshooting

**Port already in use:**
```bash
# Windows: netstat -ano | findstr :8000
# Mac/Linux: lsof -i :8000
```

**Services won't start:**
```bash
docker-compose logs api-gateway
docker-compose up --build
```
---

## Roadmap

### ✅ Completed
- [x] Microservices architecture
- [x] PostgreSQL integration
- [x] PDF processing and sentence-boundary aware chunking
- [x] Authentication and logging
- [x] Metrics and monitoring
- [x] Chroma vector database integration
- [x] Semantic search with relevance scores

### 🚧 In Progress
- [ ] `/ask` RAG endpoint (question answering with citations)

### 📅 Planned
- [ ] Document summarization
- [ ] Paper comparison
- [ ] Agent workflows (LangGraph)
- [ ] Cloud deployment
- [ ] Web UI