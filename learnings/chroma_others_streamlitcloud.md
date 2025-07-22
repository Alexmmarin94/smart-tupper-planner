# Using ChromaDB with Streamlit Cloud: Limitations, Workarounds, and Alternatives

## Context

While deploying the assistant to **Streamlit Cloud**, an unexpected error appeared when trying to use `ChromaDB` with `persist_directory`:

```text
RuntimeError: Your system has an unsupported version of sqlite3. Chroma requires sqlite3 >= 3.35.0.
```

This issue is **not related to the code or API secrets**. It is caused by **SQLite version limitations** in the base system used by Streamlit Cloud. Since you cannot upgrade SQLite there, ChromaDB fails when trying to persist the vector index.

---

## Root Cause: SQLite Version Incompatibility

ChromaDB relies on SQLite ≥ 3.35.0 to store persistent vector indexes. However:

- Streamlit Cloud uses an older version of SQLite
- You **cannot upgrade** or modify the system installation of SQLite
- Thus, any attempt to use `persist_directory=...` will fail without a workaround

---

## Workaround: Forcing Modern SQLite with `pysqlite3-binary`

A **functional workaround** exists using the `pysqlite3-binary` package, which ships its own SQLite backend.

### Steps to enable it:

1. Add this to the `requirements.txt`:
   ```text
   pysqlite3-binary
   ```

2. At the top of your the main involved scripts (`app.py`, `tupper_assistant.py`), add:
   ```python
   __import__('pysqlite3')
   import sys
   sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
   ```

3. Ensure you're using **Python 3.11** in Streamlit Cloud (set in Advanced Settings)

4. Upload the pre-generated `chroma_db/` folder (built locally) as part of the repository (or read it via a link on S3 or Huggingface Data)

This will allow Chroma to use `persist_directory` in Streamlit Cloud  
⚠️ But this hack is "unofficial" and could break with future platform changes

---

## ⚔️ ChromaDB vs. FAISS: Feature Comparison

| Feature                             | ChromaDB (no hack) | ChromaDB + `pysqlite3` | FAISS           |
|------------------------------------|---------------------|--------------------------|------------------|
| Persistent index (`persist_directory`) | ❌ Not supported     | ✅ Supported             | ✅ Supported     |
| Requires SQLite ≥ 3.35             | ✅ Yes              | ✅ Yes (forced via hack) | ❌ No (not SQLite-based) |
| Works in Streamlit Cloud           | ❌ No               | ⚠️ Yes, with override    | ✅ Yes           |
| Native LangChain integration       | ✅ Yes              | ✅ Yes                   | ✅ Yes           |
| Setup complexity                   | ⭐ Simple           | ⚠️ Medium                | ⭐⭐ Medium       |
| Best for quick demos               | ✅ In-memory mode   | ⚠️ Works with persist    | ✅ Yes           |
| Portability between environments   | ❌ Tied to SQLite   | ⚠️ Hack-dependent        | ✅ Fully portable |

---

## 🛠️ Alternative Solutions

### 🔧 Option 1: Use Chroma In-Memory (No Persist)

If persistence is not needed (e.g. for demos), simply avoid the `persist_directory` argument:

```python
vectordb = Chroma(
    embedding_function=embedding,
    collection_name="menu_platos"
)
```

✅ This works on Streamlit Cloud  
❌ But you lose the index on every app restart

---

### 🔧 Option 2: Switch to FAISS

FAISS is a reliable alternative that:

- Does not depend on SQLite
- Works in both local and cloud environments
- Requires re-generating your index from documents

Example usage:
```python
from langchain.vectorstores import FAISS

vectordb = FAISS.from_documents(docs, embedding)
```

You can also save/load the index:

```python
# Save locally
vectordb.save_local("index_path")

# Later load from file
vectordb = FAISS.load_local("index_path", embedding)
```

🔐 Store `index_path` in `st.secrets` if needed

---

### 🔧 Option 3: Pre-Generate the Index Locally and Upload

If you want to stick with ChromaDB:

1. Build the index locally with `persist_directory='chroma_db'`
2. Commit the folder to your repo
3. Deploy to Streamlit Cloud
4. Use the `pysqlite3` override at runtime

✅ Works well  
⚠️ Requires syncing local and deployed versions of `chroma_db/`

---

## Recommendation Summary

| Scenario                       | Recommended Option                          |
|--------------------------------|---------------------------------------------|
| Quick demo, no persistence     | Chroma in-memory                            |
| Full functionality in Cloud    | Chroma + `pysqlite3` hack                   |
| Maximum portability            | FAISS                                       |
| Long-term production stability | FAISS or external hosted vector store       |

---

## Final Notes

- The `pysqlite3-binary` hack works **today**, but is not officially supported
- For long-term reliability, prefer `FAISS` or externally hosted solutions like `Qdrant`, `Weaviate`, or `Pinecone`
- If you use Chroma + persist in production, **document the hack carefully**

---

## TL;DR

> Streamlit Cloud breaks ChromaDB persistency due to SQLite version limits.  
> Use `pysqlite3-binary` as a workaround, or switch to FAISS for stability.
