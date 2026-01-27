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
LIMIT 10;
```

- `<=>` = Cosine distance operator
- Returns the 10 most similar chunks

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

---

## 📚 References

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [LangChain PGVector](https://python.langchain.com/docs/integrations/vectorstores/pgvector)
