## Feedback Intelligence System

An end-to-end platform to ingest customer feedback and knowledge base (KB) docs, label them with AI, generate embeddings, index for semantic search, and answer questions via RAG and an agentic planner. Frontend is a Streamlit dashboard; backend is FastAPI with PostgreSQL + pgvector.

### Highlights
- Multi-format ingestion: CSV/JSON (feedback), TXT/MD/PDF (KB)
- AI labeling: sentiment, category, aspects (Groq LLM)
- Embeddings: BGE-small-en-v1.5 (384‑dim) with pgvector
- Unified semantic search across feedback + KB chunks
- RAG Q&A with citations and an agentic planner (stats/RAG/examples)
- Streamlit dashboard: KPIs, trends, drilldown, Ask AI/Agent

## Architecture
- Backend: FastAPI, SQLAlchemy, pgvector
- ML: SentenceTransformers (BGE), Groq LLM (model configurable via env)
- DB: PostgreSQL with pgvector extension
- Frontend: Streamlit multipage app

```
Frontend (Streamlit) ⇄ Backend (FastAPI) ⇄ PostgreSQL (+ pgvector)
                               ⇅
                        Embeddings + Groq LLM
                        RAG (Retriever + LLM)
```

## Repository Structure
```
feedback-intelligence-repo/
  backend/
    api/                # FastAPI routers (ingestion, analytics, search, rag, agent, etc.)
    services/           # Business logic (labeling, embeddings, indexer, search, rag, agent)
    database/           # SQLAlchemy models, session, Base
    ml/                 # Embedding + Groq client wrappers
    main.py             # FastAPI app entrypoint
  frontend/
    app.py              # Streamlit entry
    pages/              # Multipage dashboard (Ingest, Analytics, Ask AI/Agent, Search)
  data/                 # Sample data, taxonomy, KB folders
  models/               # Model artifacts (if any)
  requirements.txt
  env.local             # Local env variables (do NOT commit secrets)
  Readme.Md
```

## Prerequisites
- Python 3.10+
- PostgreSQL 14+ with pgvector extension
- Recommended: virtualenv or conda

## Setup

1) Create and configure the database
- Create a PostgreSQL database and enable pgvector
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

2) Environment variables
- Copy and edit `env.local` at repo root (do not commit real keys)
```
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/feedback_intel
USE_PGVECTOR=true
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=llama3-8b-8192
```

3) Install dependencies
```bash
pip install -r requirements.txt
```

4) Initialize DB (first run will auto-create tables via SQLAlchemy models)

## Run

Backend (FastAPI)
```bash
cd backend
```
- API Docs: `http://localhost:8000/docs`
- Health: GET `/`

Frontend (Streamlit)
```bash
cd frontend
streamlit run app.py
```
- Set `BACKEND_URL` env if backend not at `http://localhost:8000`.

## Key Endpoints

- Health
  - GET `/` root
- Ingestion
  - POST `/ingest/feedback` (CSV/JSON uploads)
  - POST `/ingest/docs` (TXT/MD/PDF KB docs)
- Labeling
  - POST `/labeling/batch`
  - POST `/labeling/incremental?limit=N`
- Embeddings
  - POST `/embeddings/batch?limit=N`
  - POST `/embeddings/all`
- Indexing
  - POST `/indexer/feedback`
  - POST `/indexer/kb`
- Search
  - GET `/search?query=...&top_k=...&product=...&locale=...`
- RAG
  - GET `/rag/ask?query=...&top_k=...`
- Agent (Planner: stats/RAG/examples)
  - GET `/ask/agent?query=...`

## Workflow

1) Ingest
- Upload CSV/JSON feedback → `feedback` table linked to `ingestion_runs`
- Upload KB docs → `kb_docs`, chunked into `kb_chunks` with embeddings

2) Label
- Run batch/incremental labeling to populate sentiment/category/aspects

3) Embed
- Generate 384‑d BGE embeddings for feedback; KB chunks embedded at ingestion

4) Index
- Index feedback + KB chunks into `search_index` for unified retrieval

5) Retrieve
- Semantic search or RAG via `/search` and `/rag/ask`

6) Analyze
- `/analytics/*` endpoints power the Streamlit analytics tabs

## Streamlit Pages
- Home: health and quick overview
- Ingest: upload feedback files
- Ingest & Label: ingest + labeling + embeddings
- Analytics Dashboard: KPIs, trends, drilldown, CSV export
- Ask AI (RAG): Q&A with cited sources
- Ask Agent: planner‑driven answers with stats/examples/citations
- Search Demo: unified search index exploration

## Security & Ops
- Do not commit real secrets; use `env.local` locally
- Parameterized SQL for analytics; whitelisted aggregations only
- Configurable chunk sizes, top_k, and limits
- Logging via FastAPI and service layers

## Testing Quick Guide
- Start backend and verify:
  - GET `/` returns health message
  - GET `/docs` loads Swagger UI
- Ingest sample data (CSV/JSON)
- Label → Embed → Index
- Test retrieval:
  - GET `/search?query=password reset`
  - GET `/rag/ask?query=How to reset password?`
- Open Streamlit dashboard and exercise all tabs

## Roadmap (suggested)
- Multi‑language support and language‑aware embeddings
- Reranking for better top‑k precision
- Fine‑tuned labeling for domain categories
- Role‑based access and auth
- Dockerfiles and compose for local stack

## License
MIT (or your choice)

## Acknowledgements
- SentenceTransformers BGE‑small‑en‑v1.5
- Groq LLM API
- FastAPI, SQLAlchemy, pgvector, Streamlit

Note: If any secrets were accidentally committed earlier, rotate them and remove from history. Use environment variables instead.


