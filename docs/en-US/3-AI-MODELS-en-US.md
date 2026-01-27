# 🤖 3. AI Models

DocMind uses AI at two moments: **vectorization** and **text generation**.

---

## 🧠 1. Embedding Models

Transform text into numerical vectors.
Sentences with similar meanings generate nearby vectors.

| Provider   | Default Model            | Usage                               |
| ---------- | ------------------------ | ----------------------------------- |
| **OpenAI** | `text-embedding-3-small` | Vectorization of chunks and queries |
| **Google** | `models/embedding-001`   | Vectorization of chunks and queries |

**When they are used:**

- During ingestion (converting chunks into vectors)
- During search (converting question into vector)

---

## 💬 2. Chat Models (LLM)

Generate natural language responses from the retrieved context.

| Provider   | Default Model           | Characteristic          |
| ---------- | ----------------------- | ----------------------- |
| **OpenAI** | `gpt-4o-mini`           | Fast and cost-effective |
| **Google** | `gemini-2.5-flash-lite` | Low latency             |

**Critical configuration:**

- `temperature=0` (deterministic, fewer hallucinations)
- Configurable timeout in `settings.py`

---

## 🎛️ How to Switch Models

Via environment variables in `.env`:

```ini
# Chat Models
OPENAI_CHAT_MODEL=gpt-4o
GOOGLE_CHAT_MODEL=gemini-2.0-flash

# Embedding Models
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
GOOGLE_EMBEDDING_MODEL=models/embedding-001
```

---

## ⚙️ Configuration Hierarchy

1. **`.env`** - Overrides everything (highest priority)
2. **`settings.py`** - Default values

If the variable exists in `.env`, it is used.
Otherwise, the default from `settings.py` is used.

---

## 📚 References

- [LangChain ChatOpenAI](https://python.langchain.com/docs/integrations/chat/openai/)
- [LangChain OpenAI Embeddings](https://python.langchain.com/docs/integrations/text_embedding/openai/)
- [Google Gemini Models](https://ai.google.dev/gemini-api/docs/models)
- [LangChain Google Integration](https://python.langchain.com/docs/integrations/providers/google)
