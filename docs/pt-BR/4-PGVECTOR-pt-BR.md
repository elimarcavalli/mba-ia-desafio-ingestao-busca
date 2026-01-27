# 🔍 4. Busca Semântica com pgvector

O **pgvector** é uma extensão do PostgreSQL que permite armazenar e buscar vetores.

---

## 📊 O que são Embeddings?

Representações numéricas de texto em alta dimensão.

```
"O gato pulou"     → [0.12, -0.34, 0.56, ..., 0.89]
"O felino saltou"  → [0.13, -0.33, 0.55, ..., 0.88]  ← Similares!
"Receita de bolo"  → [0.78, 0.21, -0.44, ..., 0.12]  ← Diferente
```

Textos com significado similar têm vetores próximos.

---

## 🆚 Busca Tradicional vs Semântica

| Aspecto            | Tradicional (LIKE) | Semântica (pgvector) |
| ------------------ | ------------------ | -------------------- |
| Método             | Palavras exatas    | Significado          |
| Sinônimos          | ❌ Não encontra    | ✅ Encontra          |
| Erros de digitação | ❌ Falha           | ✅ Tolera            |
| Contexto           | ❌ Ignora          | ✅ Compreende        |

**Exemplo:**

- Documento: _"O automóvel apresentou falha no sistema de freios."_
- Busca: "carro com problema nos freios"
- Tradicional: ❌ | Semântica: ✅

---

## 🔎 Query SQL do pgvector

```sql
SELECT content, 1 - (embedding <=> $1) AS similarity
FROM langchain_pg_embedding
ORDER BY embedding <=> $1
LIMIT 10;
```

- `<=>` = Operador de distância de cosseno
- Retorna os 10 chunks mais similares

---

## 🚀 Performance com HNSW

O pgvector suporta índice **HNSW** para busca aproximada:

```sql
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
```

| Volume      | Sem índice | Com HNSW |
| ----------- | ---------- | -------- |
| 10K vetores | ~50ms      | ~2ms     |
| 1M vetores  | ~5s        | ~10ms    |

---

## 📁 Arquivos Relacionados

| Arquivo                                              | Função                          |
| ---------------------------------------------------- | ------------------------------- |
| `src/infrastructure/adapters/pgvector_repository.py` | Comunicação com pgvector        |
| `docker-compose.yml`                                 | Container PostgreSQL + pgvector |

---

## 📚 Referências

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [LangChain PGVector](https://python.langchain.com/docs/integrations/vectorstores/pgvector)
