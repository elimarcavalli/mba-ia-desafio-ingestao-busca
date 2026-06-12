# 🔍 4. Semantic Search with pgvector

**pgvector** is a PostgreSQL extension that allows storing and searching vectors.

---

## 📊 What are Embeddings?

Numerical representations of text in high dimensions.

```
"The cat jumped"      → [0.12, -0.34, 0.56, ..., 0.89]
"The feline leaped"   → [0.13, -0.33, 0.55, ..., 0.88]  ← Similar!
"Cake recipe"         → [0.78, 0.21, -0.44, ..., 0.12]  ← Different
```

Texts with similar meaning have nearby vectors.

---

## 🆚 Traditional vs Semantic Search

| Aspect   | Traditional (LIKE) | Semantic (pgvector) |
| -------- | ------------------ | ------------------- |
| Method   | Exact words        | Meaning             |
| Synonyms | ❌ Doesn't find    | ✅ Finds            |
| Typos    | ❌ Fails           | ✅ Tolerates        |
| Context  | ❌ Ignores         | ✅ Understands      |

**Example:**

- Document: _"The automobile presented a failure in the brake system."_
- Search: "car with brake problem"
- Traditional: ❌ | Semantic: ✅

---

## 🔎 pgvector SQL Query

```sql
SELECT content, 1 - (embedding <=> $1) AS similarity
FROM langchain_pg_embedding
ORDER BY embedding <=> $1
LIMIT 30;
```

- `<=>` = Cosine distance operator
- DocMind fetches **30 candidates** (`fetch_k = retriever_k × 3 = 10 × 3`) and then applies **MMR** to reduce them to the final 10 with diversity.

---

## 🚀 Performance with HNSW

pgvector supports **HNSW** index for approximate search:

```sql
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
```

| Volume      | Without index | With HNSW |
| ----------- | ------------- | --------- |
| 10K vectors | ~50ms         | ~2ms      |
| 1M vectors  | ~5s           | ~10ms     |

---

## 📁 Related Files

| File                                                 | Function                        |
| ---------------------------------------------------- | ------------------------------- |
| `src/infrastructure/adapters/pgvector_repository.py` | Communication with pgvector     |
| `docker-compose.yml`                                 | PostgreSQL + pgvector container |

> ⚠️ **Known workaround:** `langchain-postgres` keeps a `scoped_session` that accumulates stale ORM objects across sequential inserts and triggers `NotNullViolation`. The `PGVectorRepository._reset_session()` method calls `session_maker.remove()` before each insert to work around this — see `pgvector_repository.py:29-37`.

---

## 📚 References

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [LangChain PGVector](https://python.langchain.com/docs/integrations/vectorstores/pgvector)
