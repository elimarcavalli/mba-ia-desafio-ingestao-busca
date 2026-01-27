# 🤖 3. Modelos de IA

O DocMind usa IA em dois momentos: **vetorização** e **geração de texto**.

---

## 🧠 1. Modelos de Embedding

Transformam texto em vetores numéricos.
Frases com significados similares geram vetores próximos.

| Provedor   | Modelo Padrão            | Uso                             |
| ---------- | ------------------------ | ------------------------------- |
| **OpenAI** | `text-embedding-3-small` | Vetorização de chunks e queries |
| **Google** | `models/embedding-001`   | Vetorização de chunks e queries |

**Quando são usados:**

- Na ingestão (converter chunks em vetores)
- Na busca (converter pergunta em vetor)

---

## 💬 2. Modelos de Chat (LLM)

Geram respostas em linguagem natural a partir do contexto recuperado.

| Provedor   | Modelo Padrão           | Característica           |
| ---------- | ----------------------- | ------------------------ |
| **OpenAI** | `gpt-4o-mini`           | Rápido e custo-eficiente |
| **Google** | `gemini-2.5-flash-lite` | Baixa latência           |

**Configuração crítica:**

- `temperature=0` (determinístico, menos alucinações)
- Timeout configurável em `settings.py`

---

## 🎛️ Como Trocar de Modelo

Via variáveis de ambiente no `.env`:

```ini
# Modelos de Chat
OPENAI_CHAT_MODEL=gpt-4o
GOOGLE_CHAT_MODEL=gemini-2.0-flash

# Modelos de Embedding
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
GOOGLE_EMBEDDING_MODEL=models/embedding-001
```

---

## ⚙️ Hierarquia de Configuração

1. **`.env`** - Sobrescreve tudo (prioridade máxima)
2. **`settings.py`** - Valores padrão

Se a variável existe no `.env`, ela é usada.
Caso contrário, usa-se o padrão do `settings.py`.

---

## 📚 Referências

- [LangChain ChatOpenAI](https://python.langchain.com/docs/integrations/chat/openai/)
- [LangChain OpenAI Embeddings](https://python.langchain.com/docs/integrations/text_embedding/openai/)
- [Google Gemini Models](https://ai.google.dev/gemini-api/docs/models)
- [LangChain Google Integration](https://python.langchain.com/docs/integrations/providers/google)
