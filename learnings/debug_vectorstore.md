# Debugging Vectorstore Issues with Chroma and LangChain

This document outlines the key problems encountered during the construction and persistence of a vectorstore using `Chroma` and `LangChain`, and explains how to avoid them in future projects.

---

## TL;DR – What Went Wrong and How We Fixed It

Two main issues:

1. ❌ **Passing `id=` to `Document(...)`**, which is not a valid parameter and silently prevents metadata from being persisted.  
2. ❌ **Using poor `page_content` (e.g., only `ingredientes`)**, leading to meaningless embeddings and zero search hits.

We also encountered:

- ❌ A locked or corrupted Chroma DB when trying to overwrite the vectorstore.

---

## Problem 1: Using `id=` in the Document Constructor

### ❌ Faulty Code

```python
docs.append(Document(
    page_content=...,
    metadata=...,
    id=str(r["nombre_plato"])  # Invalid
))
```

### Issue

- `id` is not a recognized argument in `langchain.schema.Document`.
- This can cause metadata to **disappear silently** when persisting to Chroma.

### Solution

- Remove `id=...` entirely.
- If you want to preserve the identifier, include it as part of `metadata`:

```python
metadata["id"] = str(r["nombre_plato"])
```

---

## Problem 2: Embedding Only `ingredientes` as Content

### ❌ Faulty Code

```python
docs.append(Document(
    page_content=str(r["ingredientes"]),
    metadata=...
))
```

### Issue

- Using only the ingredient list lacks semantic context.
- Leads to **poor vector representations** and irrelevant search results.

### Solution

Build a rich and descriptive `page_content`:

```python
content = (
    f"Nombre del plato: {r['nombre_plato']}. "
    f"Ingredientes: {r['ingredientes']}. "
    f"Alergenos: {r['alergenos']}. "
    f"Precio: {r['precio']} euros. "
    f"Kcal: {r['kcal']}, Proteínas: {r['proteinas']}, "
    f"Hidratos: {r['hidratos']}, Grasas: {r['grasas']}, Peso: {r['peso']}g."
)
docs.append(Document(page_content=content, metadata=metadata))
```

---

## Bonus: Read-Only Database Errors

### Symptom

```
InternalError: Query error: Database error: error returned from database: (code: 1032) attempt to write a readonly database
```

### Issue

- Happens when trying to write to an existing Chroma DB that is locked, corrupted, or improperly closed.

### Solution

- Manually delete the vectorstore folder before writing:

```python
import shutil
shutil.rmtree("chroma_db")
```

- Restart the Python kernel if needed to fully release any locks.

---

## Final Best Practices

- ✅ Use a **rich `page_content`** with full semantic detail.
- ✅ **Never use `id=`** in `Document(...)`.
- ✅ Clear previous vectorstore state before writing new documents.
- ✅ Use `.get()` to verify that both documents and metadata are being correctly persisted.

---

## Code to Verify Before Using the Vector DB

Before proceeding to retrieval, QA, or chatbot integration, use the following snippet to validate that your documents are properly indexed:

```python
from langchain_chroma.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vectordb = Chroma(
    persist_directory="chroma_db",
    embedding_function=embedding,
    collection_name="menu_platos"
)

docs = vectordb.similarity_search("plato", k=10)

for i, d in enumerate(docs, 1):
    print(f"\n📄 Document {i}")
    print(f"Content: {d.page_content[:100]}...")
    print(f"Metadata: {d.metadata}")
```
