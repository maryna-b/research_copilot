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
- ✅ Intelligent text chunking
- ✅ Metadata storage in PostgreSQL

### Infrastructure
- ✅ API key authentication
- ✅ Structured logging with request IDs
- ✅ Prometheus metrics and monitoring
- ✅ Comprehensive error handling
- ✅ Input validation
- ✅ Docker containerization

### Coming Soon 
- 🚧 Vector embeddings with Chroma
- 🚧 Semantic search
- 🚧 Question answering with LangChain
- 🚧 Source citations and references

---

## Architecture

### Current 

```
Client → API Gateway → Ingestion Service → PostgreSQL
            ↓
       Authentication
       Logging
       Metrics
```

### Target

```
Client → API Gateway ┬→ Ingestion Service → PostgreSQL
                     │                    ↓
                     │                  Chroma (Embeddings)
                     │                    ↑
                     └→ Query Service ────┘
                        (LangChain + LLM)
```

**Services:**
- **API Gateway** (Port 8000) - Routing, authentication, logging
- **Ingestion Service** (Port 8001) - PDF processing, text extraction
- **Query Service** (Port 8003) - Semantic search, QA *(Week 2)*
- **PostgreSQL** (Port 5432) - Document metadata
- **Chroma** (Port 8002) - Vector embeddings *(Week 2)*

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ for local development

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
- `GET /info` - Service information

**Authentication:** Include header `X-API-Key: key`

## Tech Stack

### Current 
- **FastAPI** - Async web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM
- **pdfplumber** - PDF text extraction
- **Prometheus** - Metrics
- **Docker Compose** - Container orchestration

### Planned 
- **Chroma** - Vector database
- **Sentence Transformers / OpenAI** - Text embeddings
- **LangChain** - LLM orchestration
- **LangGraph** - Multi-agent workflows
- **OpenAI GPT-3.5/4** - Question answering

---

## Local Development (No Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=research_user \
  -e POSTGRES_PASSWORD=research_pass \
  -e POSTGRES_DB=research_db \
  postgres:15-alpine

# Run services (separate terminals)
cd services/ingestion_service && uvicorn main:app --reload --port 8001
cd services/api_gateway && uvicorn main:app --reload --port 8000
```

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

See [Metrics Guide](./documentation/METRICS_GUIDE.md) for details.

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
- [x] PDF processing and chunking
- [x] Authentication and logging
- [x] Metrics and monitoring

### 🚧 In Progress 
- [ ] Chroma vector database
- [ ] Semantic search
- [ ] Question answering with LangChain
- [ ] Citation tracking

### 📅 Planned
- [ ] Document summarization
- [ ] Paper comparison
- [ ] Agent workflows (LangGraph)
- [ ] Cloud deployment
- [ ] Web UI

---

## License

MIT