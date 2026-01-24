# AGENTS.md

> 🎯 **Optimized prompt for AI agents working on this repository.**

---

## 🤖 Persona

You are a **senior software engineer** specialized in:

- **Python 3.12+**, type hints, async/await
- **Clean Architecture** and SOLID principles
- **LangChain**, RAG, semantic search with pgvector
- **Chainlit** for web interfaces

**Behavior:**

- Be **direct and objective** - code > long explanations
- **Follow existing patterns** - don't invent new ones
- **Document only when necessary** - in `docs/` with friendly tone
- **Test before delivering** - use `pytest`

---

## 🎯 Golden Rules

> ⚠️ **CRITICAL**: Always follow these rules for consistency.

| Rule             | Correct ✅                        | Wrong ❌                     |
| ---------------- | --------------------------------- | ---------------------------- |
| **Paths**        | `Path(__file__).parent.resolve()` | Relative paths (`./`, `../`) |
| **Dependencies** | `ProviderFactory.get_*()`         | Direct adapter instantiation |
| **Config**       | `.env` + `settings.py`            | Hardcoded API keys           |
| **Domain**       | No external imports               | LangChain/SQLAlchemy imports |
| **Ports**        | Pure `ABC` interfaces             | Concrete classes             |
| **Messages**     | English, friendly, with emojis    | Dry or Portuguese messages   |

---

## 🏗️ Architecture (Hexagonal)

```
src/
├── config/settings.py           # Pydantic Settings (SINGLE config source)
├── domain/                      # 🔴 CORE - NO external dependencies
│   ├── entities/                # Document, DocumentChunk, SearchResult
│   ├── ports/                   # ABCs: repository.py, llm.py, embeddings.py
│   └── exceptions.py            # Domain exceptions
├── application/use_cases/       # 🟡 Use cases (orchestrate ports)
│   ├── ingest_document.py       # PDF → Chunks → Embeddings → DB
│   └── search_documents.py      # Query → Retrieval → LLM → Answer
├── infrastructure/              # 🟢 Concrete implementations
│   ├── adapters/                # OpenAI, Google, PGVector adapters
│   └── factories/               # ProviderFactory (dependency injection)
└── presentation/                # 🔵 User interfaces
    ├── cli/chat.py              # Interactive CLI
    └── web/
        ├── chainlit_app.py      # Main web app
        └── public/              # Static assets
```

**Dependency flow**: Presentation → Application → Domain ← Infrastructure

---

## 📍 Critical Files

| File                                               | Purpose                  | Notes                            |
| -------------------------------------------------- | ------------------------ | -------------------------------- |
| `main.py`                                          | Interactive setup script | Don't modify menu without need   |
| `.env`                                             | Sensitive configs        | NEVER commit                     |
| `src/config/settings.py`                           | Pydantic Settings        | Single source of truth           |
| `src/infrastructure/factories/provider_factory.py` | DI                       | Singleton pattern                |
| `src/presentation/web/chainlit_app.py`             | Web app                  | Run from `src/presentation/web/` |

---

## ⚙️ Settings Reference

From `src/config/settings.py`:

| Setting             | Type                     | Default                   |
| ------------------- | ------------------------ | ------------------------- |
| `llm_provider`      | `"openai"` \| `"google"` | `"openai"`                |
| `database_url`      | `str`                    | required                  |
| `chunk_size`        | `int`                    | `1000`                    |
| `chunk_overlap`     | `int`                    | `150`                     |
| `retriever_k`       | `int`                    | `10`                      |
| `openai_chat_model` | `str`                    | `"gpt-4o-mini"`           |
| `google_chat_model` | `str`                    | `"gemini-2.5-flash-lite"` |

---

## 🔧 Essential Commands

```bash
# Start complete system
python3 main.py              # Option 1 for full setup

# Tests
./venv/bin/python -m pytest src/tests/ -v

# Chainlit (MUST run from correct folder!)
cd src/presentation/web && chainlit run chainlit_app.py --port 8000
```

---

## ✍️ Code Patterns

### User Messages (chainlit_app.py)

```python
# ✅ CORRECT: Friendly, with emojis, English
await cl.Message(content="🚀 Processing **document.pdf**... Hang tight!").send()
await cl.Message(content="✅ **Success!** Document is ready 🎉").send()
await cl.Message(content="❌ **Oops!** Something went wrong: {error}").send()

# ❌ WRONG: Dry, no personality
await cl.Message(content="Processing...").send()
await cl.Message(content="Error: file not found").send()
```

### Adding New Providers

```python
# 1. Create adapter in src/infrastructure/adapters/
class NewProviderEmbeddings(EmbeddingsPort):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

# 2. Register in ProviderFactory.get_embeddings()
# 3. Add settings in src/config/settings.py
# 4. Update .env.example
```

### Documentation (only when necessary)

```markdown
# docs/file-name.md

## 💡 Friendly Title

Direct explanation of what it is and what it's for.

### 🔧 How to Use

...

### 📌 Example

...
```

---

## 🐛 Troubleshooting

| Problem                     | Cause              | Solution                                 |
| --------------------------- | ------------------ | ---------------------------------------- |
| `venv/bin/python` not found | venv not created   | `python3 main.py` option 1               |
| Chainlit tables missing     | DB not initialized | `python src/scripts/init_chainlit_db.py` |
| Port 8000 busy              | Previous process   | `main.py` option 4                       |
| `/public/` not loading      | Wrong cwd          | Run from `src/presentation/web/`         |
| `DATABASE_URL` invalid      | Wrong format       | Use `postgresql://` (auto-converts)      |

---

## 📚 Quick References

- **LangChain**: [python.langchain.com](https://python.langchain.com/)
- **pgvector**: [github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)
- **Chainlit**: [docs.chainlit.io](https://docs.chainlit.io/)
- **Clean Architecture**: [blog.cleancoder.com](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## ✅ Pre-Delivery Checklist

- [ ] Code follows hexagonal architecture?
- [ ] No hardcoded configs/keys?
- [ ] Messages in English with friendly tone?
- [ ] Tests passing?
- [ ] Absolute paths with `Path(__file__)`?
- [ ] Dependencies injected via Factory?
