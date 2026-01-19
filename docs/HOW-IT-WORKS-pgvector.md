# 🔍 Como Funciona a Busca Semântica com pgvector

## Visão Geral

Este documento explica como o sistema utiliza **PostgreSQL + pgvector** para realizar buscas semânticas em documentos PDF.

---

## 1. Experiência do Usuário

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Upload       2. Processamento      3. Pergunta   4. Resposta│
│  ──────────      ───────────────       ──────────   ────────────│
│  📄 PDF    →    ⚙️ Indexação      →    💬 Query  →   🎯 Resultado│
│                  (automático)                                    │
└─────────────────────────────────────────────────────────────────┘
```

1. **Upload**: Usuário envia um PDF
2. **Processamento**: Sistema divide, vetoriza e armazena (5-30 segundos)
3. **Pergunta**: Usuário faz perguntas em linguagem natural
4. **Resposta**: Sistema encontra contexto relevante e gera resposta

---

## 2. Fluxo Técnico

### 2.1 Ingestão de Documentos

```
PDF → Parser → Chunks → Embedding API → Vetores → PostgreSQL
```

| Etapa | Componente | Descrição |
|-------|------------|-----------|
| 1 | PyPDF | Extrai texto do PDF |
| 2 | TextSplitter | Divide em chunks de ~500 tokens |
| 3 | OpenAI/Gemini API | Converte texto → vetor 1536D |
| 4 | pgvector | Armazena vetores com indexação |

**Código real** (`IngestDocumentUseCase`):
```python
# 1. Extrai texto
loader = PyPDFLoader(pdf_path)
documents = loader.load()

# 2. Divide em chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500)
chunks = splitter.split_documents(documents)

# 3-4. Vetoriza e armazena (LangChain + pgvector)
PGVector.from_documents(chunks, embeddings, connection=db_url)
```

### 2.2 Busca Semântica

```
Pergunta → Embedding → Query Vetorial → Top K Chunks → LLM → Resposta
```

**Query SQL gerada pelo pgvector**:
```sql
SELECT content, 1 - (embedding <=> $1) AS similarity
FROM langchain_pg_embedding
ORDER BY embedding <=> $1
LIMIT 5;
```

- `<=>` = Operador de **distância de cosseno**
- Retorna os 5 chunks mais semanticamente similares

---

## 3. O que são Embeddings?

Embeddings são **representações numéricas** de texto em um espaço vetorial de alta dimensão.

```
"O gato pulou"     → [0.12, -0.34, 0.56, ..., 0.89]  (1536 números)
"O felino saltou"  → [0.13, -0.33, 0.55, ..., 0.88]  (vetores similares!)
"Receita de bolo"  → [0.78, 0.21, -0.44, ..., 0.12]  (vetor diferente)
```

**Propriedade chave**: Textos com significado similar têm vetores próximos.

---

## 4. Por que pgvector?

### Comparação: Busca Tradicional vs Semântica

| Aspecto | Busca Tradicional (LIKE/FTS) | Busca Semântica (pgvector) |
|---------|------------------------------|---------------------------|
| **Método** | Palavras-chave exatas | Significado/contexto |
| **Query** | "carro vermelho" | "veículo de cor escarlate" ✓ |
| **Sinônimos** | ❌ Não encontra | ✅ Encontra |
| **Erros de digitação** | ❌ Falha | ✅ Tolera |
| **Contexto** | ❌ Ignora | ✅ Compreende |

### Exemplo Prático

**Documento**: *"O automóvel apresentou falha no sistema de freios ABS."*

| Busca | Tradicional | Semântica |
|-------|-------------|-----------|
| "carro com problema nos freios" | ❌ Não encontra | ✅ Encontra |
| "veículo com defeito" | ❌ Não encontra | ✅ Encontra |
| "automóvel falha freios" | ✅ Encontra | ✅ Encontra |

---

## 5. Integração com IA (RAG)

O sistema implementa **RAG** (Retrieval-Augmented Generation):

```
┌─────────────────────────────────────────────────────────────┐
│                         RAG Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Pergunta ──→ Embedding ──→ pgvector ──→ Top K Chunks     │
│                                              │               │
│                                              ▼               │
│   Resposta ←── LLM (GPT/Gemini) ←── Prompt + Contexto      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Benefícios do RAG**:
- ✅ LLM responde apenas com base nos documentos
- ✅ Evita "alucinações" (informações inventadas)
- ✅ Conhecimento atualizado (não depende do treinamento do modelo)

---

## 6. Performance e Escalabilidade

### Índice HNSW

O pgvector suporta **HNSW** (Hierarchical Navigable Small World), um algoritmo de busca aproximada:

```sql
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
```

| Volume de Dados | Tempo de Busca (sem índice) | Com HNSW |
|-----------------|----------------------------|----------|
| 10K vetores | ~50ms | ~2ms |
| 1M vetores | ~5s | ~10ms |
| 10M vetores | ~50s | ~20ms |

---

## 7. Arquivos-Chave do Sistema

| Arquivo | Responsabilidade |
|---------|------------------|
| `src/infrastructure/adapters/pgvector_repository.py` | Comunicação com pgvector |
| `src/application/use_cases/ingest_document.py` | Pipeline de ingestão |
| `src/application/use_cases/search_documents.py` | Pipeline de busca |
| `docker-compose.yml` | PostgreSQL + pgvector container |

---

## Referências

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [LangChain PGVector](https://python.langchain.com/docs/integrations/vectorstores/pgvector)
