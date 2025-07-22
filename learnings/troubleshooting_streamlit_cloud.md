## Troubleshooting: Chroma / sqlite3 error on Streamlit Cloud

If you're deploying a LangChain app using **Chroma** on **Streamlit Cloud**, you may run into this error:

```bash
RuntimeError: Your system has an unsupported version of sqlite3. Chroma requires sqlite3 >= 3.35.0.
```

This happens because Streamlit Cloud typically uses an older SQLite version incompatible with Chroma.

---

### ✅ Solution (confirmed working as of July 2025)

Follow these steps in order:

---

### 1. Add `pysqlite3-binary` to your `requirements.txt`

```txt
pysqlite3-binary
```

---

### 2. Patch `sqlite3` manually before any Chroma usage

At the **top** of your Python script (e.g. `app.py` or `tupper_assistant.py`), add:

```python
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
```

> ⚠️ This must appear **before** any import that relies on `sqlite3`, including `chromadb` or `langchain_chroma`.

---

### 3. Set Python version to 3.11 in Streamlit Cloud

When deploying, go to:

- **Advanced Settings → Python Version** → select **3.11**

This avoids incompatibilities between `pysqlite3` and system Python.

---

### 4. Clean and redeploy

If you had already deployed the app:

- Delete it from Streamlit Cloud
- Redeploy it from scratch using the updated `requirements.txt` and code

---

### (Optional) Clean up LangChain deprecation warnings

Replace:

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
```

With:

```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
```

This avoids future issues as LangChain evolves.

---

### ✅ Final Result

After these changes:

- ✅ Works locally
- ✅ Works on Streamlit Cloud
- ✅ Compatible with Chroma and modern SQLite

```python
# Minimal working patch (top of app.py)
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
```
