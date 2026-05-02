# AGENTS.md

This file provides guidance to AI Agents when working with code in this repository.

## Persona

Act as a **senior software engineer** specialized in Python 3.12+, Clean Architecture, LangChain/RAG, and Chainlit. Be direct and objective — code over long explanations. Follow existing patterns, don't invent new ones. Document only when necessary. Test before delivering.

## Project Overview

DocMind is a RAG (Retrieval-Augmented Generation) semantic search system that transforms documents into an intelligent Q&A assistant. Supports PDF, TXT, CSV, HTML, JSON, Markdown, and DOCX. Built with Python 3.12+, LangChain, PostgreSQL/pgvector, and Chainlit.

## Commands

```bash
# Full system setup (interactive menu: venv, deps, Docker, launch)
python3 main.py

# Run tests
./venv/bin/python -m pytest src/tests/ -v

# Run a single test file
./venv/bin/python -m pytest src/tests/unit/test_entities.py -v

# Run tests with coverage
./venv/bin/python -m pytest src/tests/ --cov=src --cov-report=term-missing

# Start Chainlit web app (MUST run from src/presentation/web/)
cd src/presentation/web && chainlit run chainlit_app.py --port 8000

# Docker (PostgreSQL + pgvector)
docker compose up -d

# Initialize Chainlit DB schema
python src/scripts/init_chainlit_db.py

# CLI chat (alternative to web UI, runs from project root)
./venv/bin/python src/presentation/cli/chat.py

# Install dependencies manually (if not using main.py)
./venv/bin/pip install -r requirements.txt
```

## Architecture (Hexagonal / Clean Architecture)

**Dependency flow:** `Presentation → Application → Domain ← Infrastructure`

- **`src/domain/`** — Pure business logic, NO external imports (no LangChain, no SQLAlchemy). Contains entities (`Document`, `DocumentChunk`, `SearchResult`), abstract port interfaces (ABCs for `RepositoryPort`, `LLMPort`, `EmbeddingsPort`, `DocumentLoaderPort`), and domain exceptions.
- **`src/application/use_cases/`** — Orchestrates ports. Two use cases: `IngestDocumentUseCase` (document → chunks → embeddings → DB) and `SearchDocumentsUseCase` (query → retrieval → LLM → answer).
- **`src/application/dto/`** — Response DTOs (`SearchResponse`) for structuring use case output.
- **`src/infrastructure/`** — Concrete adapter implementations (OpenAI, Google, PGVector, MultiFormatDocumentLoader). `ProviderFactory` in `factories/` is a singleton that handles all dependency injection — always use `ProviderFactory.get_*()`, never instantiate adapters directly.
- **`src/presentation/web/`** — Chainlit web UI (`chainlit_app.py`). Must be run from its own directory for static assets to load.
- **`src/presentation/cli/`** — Interactive CLI chat (`chat.py`). Alternative to web UI, runs from project root.
- **`src/config/settings.py`** — Single source of truth for all configuration via Pydantic `BaseSettings` (reads from `.env`). The `sqlalchemy_database_url` property converts `postgresql://` to `postgresql+psycopg://` for SQLAlchemy/LangChain compatibility.

## Key Conventions

- **Paths:** Always use `Path(__file__).parent.resolve()`, never relative paths (`./`, `../`)
- **Dependencies:** Always obtain via `ProviderFactory.get_*()`, never instantiate adapters directly
- **Config:** All settings go through `.env` + `settings.py`, never hardcode values
- **Domain isolation:** `src/domain/` must never import from LangChain, SQLAlchemy, or any framework
- **Ports:** Define as pure `ABC` interfaces, never as concrete classes
- **User-facing messages:** English, friendly tone, with emojis
- **Tests:** Use mock ports from `src/tests/conftest.py` fixtures (`mock_embeddings`, `mock_llm`, `mock_repository`, `mock_document_loader`). Call `ProviderFactory.reset()` between tests to clear cached singleton instances.

## Adding a New LLM Provider

1. Create adapter in `src/infrastructure/adapters/` implementing the relevant port (`EmbeddingsPort`, `LLMPort`)
2. Register in `ProviderFactory` (`get_embeddings()` / `get_llm()`)
3. Add settings in `src/config/settings.py`
4. Update `.env.example`

## Adding a New Document Format

1. Add the loader lambda to `_LOADERS` dict in `src/infrastructure/adapters/document_loader.py`
2. Add any new pip dependency to `requirements.txt`
3. Add the MIME type to `SUPPORTED_MIMES` in `chainlit_app.py` (extensions are auto-derived from the loader)

## Settings Reference

| Setting             | Type                     | Default                   |
| ------------------- | ------------------------ | ------------------------- |
| `llm_provider`      | `"openai"` \| `"google"` | `"openai"`                |
| `database_url`      | `str`                    | required                  |
| `chunk_size`        | `int`                    | `1000`                    |
| `chunk_overlap`     | `int`                    | `150`                     |
| `retriever_k`       | `int`                    | `15`                      |
| `openai_chat_model` | `str`                    | `"gpt-4o-mini"`           |
| `google_chat_model` | `str`                    | `"gemini-2.5-flash-lite"` |

## Code Patterns

### User Messages (chainlit_app.py)

```python
# Correct: friendly, with emojis, English
await cl.Message(content="🚀 Processing **document.pdf**... Hang tight!").send()
await cl.Message(content="✅ **Success!** Document is ready 🎉").send()
await cl.Message(content="❌ **Oops!** Something went wrong: {error}").send()

# Wrong: dry, no personality
await cl.Message(content="Processing...").send()
await cl.Message(content="Error: file not found").send()
```

## Infrastructure

- **Database:** PostgreSQL 17 with pgvector extension, runs via Docker on port 5432
- **LLM providers:** OpenAI (`gpt-4o-mini` / `text-embedding-3-small`) or Google (`gemini-2.5-flash-lite` / `embedding-001`), configured via `LLM_PROVIDER` env var
- **Web UI:** Chainlit on port 8000
- **RAG tuning env vars:** `CHUNK_SIZE` (default 1000), `CHUNK_OVERLAP` (default 150), `RETRIEVER_K` (default 15), `LLM_TIMEOUT` (default 60s)

## Troubleshooting

| Problem                     | Cause              | Solution                                 |
| --------------------------- | ------------------ | ---------------------------------------- |
| `venv/bin/python` not found | venv not created   | `python3 main.py` option 1               |
| Chainlit tables missing     | DB not initialized | `python src/scripts/init_chainlit_db.py` |
| Port 8000 busy              | Previous process   | `main.py` option 4                       |
| `/public/` not loading      | Wrong cwd          | Run from `src/presentation/web/`         |
| `DATABASE_URL` invalid      | Wrong format       | Use `postgresql://` (auto-converts)      |

## Pre-Delivery Checklist

- [ ] Code follows hexagonal architecture?
- [ ] No hardcoded configs/keys?
- [ ] Messages in English with friendly tone and emojis?
- [ ] Tests passing (`./venv/bin/python -m pytest src/tests/ -v`)?
- [ ] Absolute paths with `Path(__file__).parent.resolve()`?
- [ ] Dependencies injected via `ProviderFactory.get_*()`?

## Gotchas

- **PGVector session bug:** `langchain-postgres` scoped_session accumulates stale ORM objects across sequential inserts, causing `NotNullViolation`. The `PGVectorRepository._reset_session()` method works around this by calling `session_maker.remove()` before each insert. Do not remove it.
- **Chainlit working directory:** `chainlit_app.py` must be launched from `src/presentation/web/` (not project root) or static assets and icons won't load.
- **`docker compose up -d` must run before** any command that touches the database (ingestion, search, Chainlit). The `bootstrap_vector_ext` service auto-creates the `vector` extension on first start.
