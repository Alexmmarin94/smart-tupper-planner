# Deployment Considerations: ChromaDB Hosting in Streamlit Apps

## Context

This project uses a local `Chroma` vectorstore (`chroma_db/`) to store the embeddings of all dish documents for retrieval-based recommendations.

Given the relatively small size of the index (under 50MB), we explored various deployment strategies for compatibility with **Streamlit Community Cloud** and lightweight hosting environments.

---

## Current Strategy: GitHub-Based Deployment

Since `chroma_db/` weighs less than 50MB, we opted for the **simplest and most robust solution**: committing the entire folder to the GitHub repo.

This allows seamless deployment to **Streamlit Cloud** without modifying the codebase.

```python
# utils/tupper_assistant.py (original, unmodified)
chroma_path = base_dir.parent / "chroma_db"

vectordb = Chroma(
    persist_directory=str(chroma_path),
    embedding_function=embedding,
    collection_name="menu_platos"
)
```

No runtime logic  
Reproducible  
Works out of the box with `pysqlite3-binary` workaround

---

## ⚠️ Alternative 1: Hosting ChromaDB on Hugging Face Datasets

If the vectorstore exceeded GitHub's file size limits (e.g. >50MB total or >100MB per file), we considered uploading a zipped version of `chroma_db/` to Hugging Face Datasets and dynamically downloading + extracting it at runtime:

```python
# utils/tupper_assistant.py (Hugging Face hosting)
import requests, zipfile

chroma_path = base_dir.parent / "chroma_db"
zip_url = "https://huggingface.co/datasets/<user>/<repo>/resolve/main/chroma_db.zip"
zip_path = base_dir.parent / "chroma_db.zip"

if not chroma_path.exists():
    with open(zip_path, "wb") as f:
        f.write(requests.get(zip_url).content)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(chroma_path)

vectordb = Chroma(
    persist_directory=str(chroma_path),
    embedding_function=embedding,
    collection_name="menu_platos"
)
```

Keeps the GitHub repo lightweight  
⚠️ Adds external dependency and delay at app start

---

## ⚠️ Alternative 2: Rebuilding the Vectorstore from CSV at Runtime

As a fallback, we can rebuild the ChromaDB from `df_final_official.csv` (the final annotated dataset) entirely at runtime. This avoids hosting any binary index but increases load time significantly.

```python
# utils/tupper_assistant.py (build Chroma from CSV)
import pandas as pd
from langchain_core.documents import Document

df = pd.read_csv(base_dir.parent / "data/df_final_official.csv").fillna({"ingredientes": "", "alergenos": ""})

docs = []
for _, r in df.iterrows():
    content = (
        f"Nombre del plato: {r['nombre_plato']}. "
        f"Ingredientes: {r['ingredientes']}. "
        f"Alergenos: {r['alergenos']}"
    )
    docs.append(Document(page_content=content, metadata=r.to_dict()))

vectordb = Chroma.from_documents(
    documents=docs,
    embedding=embedding,
    persist_directory=str(base_dir.parent / "chroma_db")
)
```

⚠️ Slower boot time  
⚠️ Rebuilds on every app restart unless cache is used  
✅ Good for prototyping or constrained deployments

---

## 📌 Summary: Deployment Options for ChromaDB

| Strategy                          | Setup Required | Load Time | Code Simplicity | Cloud-Friendly | Ideal For                  |
|----------------------------------|----------------|-----------|------------------|----------------|----------------------------|
| GitHub Commit (current)          | ✅ Minimal      | ✅ Fast    | ✅ Clean          | ✅ Yes         | Small vectorstores         |
| Hugging Face Hosting (zip)       | ⚠️ Moderate     | ⚠️ Medium  | ⚠️ Needs logic    | ✅ Yes         | Medium-size deployments    |
| Rebuild from CSV                 | ⚠️ High         | ❌ Slow    | ✅ Transparent    | ✅ Yes         | Rapid prototyping, fallback |

---

## ✅ Conclusion

The current strategy (direct GitHub commit) is optimal for this use case.

However, the pipeline remains flexible and can easily pivot to Hugging Face hosting or runtime rebuilding if future scale or platform constraints require it.
