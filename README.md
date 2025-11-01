# Research Copilot

A microservices-based AI research assistant for ingesting, processing, and querying research papers and documents.

## Features

- PDF document upload and processing
- Text extraction and intelligent chunking
- Document metadata management
- RESTful API with OpenAPI documentation
- Metrics and health monitoring
- Secure API key authentication

## Architecture

The system consists of microservices communicating over HTTP:

- **API Gateway** - Entry point for client requests, handles routing and authentication
- **Ingestion Service** - PDF processing, text extraction, and chunk generation
- **PostgreSQL** - Document metadata and processing state storage

## Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)

## Quick Start

### Using Docker Compose

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your configuration (API keys, database credentials)

3. Start all services:
   ```bash
   docker-compose up --build
   ```

4. Access the APIs:
   - API Gateway: http://localhost:8000/docs
   - Ingestion Service: http://localhost:8001/docs

### Local Development

1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run services individually:
   ```bash
   # Terminal 1 - API Gateway
   cd services/api_gateway
   uvicorn main:app --reload --port 8000

   # Terminal 2 - Ingestion Service
   cd services/ingestion_service
   uvicorn main:app --reload --port 8001
   ```

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Upload Document
```bash
curl -X POST http://localhost:8000/upload \
  -H "x-api-key: your_api_key" \
  -F "file=@document.pdf"
```

Response:
```json
{
  "document_id": "uuid",
  "filename": "document.pdf",
  "chunks": [
    {
      "chunk_id": 0,
      "text": "...",
      "page": 1
    }
  ],
  "total_chunks": 10
}
```

## Monitoring

Prometheus metrics are exposed at:
- API Gateway: http://localhost:8000/metrics
- Ingestion Service: http://localhost:8001/metrics

## Configuration

Configuration is managed through environment variables. See `.env.example` for available options:

- `API_KEY` - API authentication key
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` - Database credentials
- `INGESTION_SERVICE_URL` - Internal service URL for Docker Compose

## Tech Stack

- **FastAPI** - Async web framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Relational database
- **Pydantic** - Data validation
- **pdfplumber** - PDF text extraction
- **Prometheus** - Metrics collection
- **Docker** - Containerization

## License

MIT
