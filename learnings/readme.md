# Learnings Archive

This folder gathers key lessons, design rationales, and debugging notes compiled during the development of this project. Each document captures insights that go beyond the immediate technical implementation — from architectural decisions to deployment workarounds, model behavior, and the role of data science intuition.

---

## Architecture & Design Decisions

- **[`agentic_or_not.md`](./agentic_or_not.md)**  
  Explores whether the assistant qualifies as an "agent", and compares deterministic pipelines vs. agentic systems.

- **[`prompt_pipeline_vs_agentic_architecture.md`](./prompt_pipeline_vs_agentic_architecture.md)**  
  Contrasts prompt-based workflows (`filter_prompt + qa_prompt`) with agent-driven architectures, outlining tradeoffs in modularity, cost, and scalability.

- **[`filterprompt_vs_qaprompt.md`](./filterprompt_vs_qaprompt.md)**  
  Justifies the two-prompt structure and its benefits in control, interpretability, and filtering accuracy.

- **[`pagecontent_vs_metadata.md`](./pagecontent_vs_metadata.md)**  
  Clarifies the distinction and interplay between `page_content` and `metadata` in RAG systems.

---

## Debugging Notes

- **[`debug_vectorstore.md`](./debug_vectorstore.md)**  
  Chronicles key mistakes (e.g., misuse of `id=`, poor `page_content`) and how they silently break Chroma indexing or degrade semantic search quality.

- **[`debugging_incoherent_answers.md`](./debugging_incoherent_answers.md)**  
  Addresses long, unfocused answers and model blindness to metadata, with prompt and formatting fixes that improved alignment.

---

## Vectorstore Setup & Deployment

- **[`chroma_others_streamlitcloud.md`](./chroma_others_streamlitcloud.md)**  
  Covers the limitations of ChromaDB on Streamlit Cloud, the `pysqlite3` workaround, and comparison with FAISS.

- **[`troubleshooting_streamlit_cloud.md`](./troubleshooting_streamlit_cloud.md)**  
  Focused step-by-step fix for `sqlite3` incompatibilities when deploying LangChain + Chroma.

- **[`VectorialDB_deploy_options.md`](./VectorialDB_deploy_options.md)**  
  Evaluates hosting options: GitHub commit, Hugging Face zip download, or full runtime rebuild from CSV.

---

## Model Ecosystem & Future Work

- **[`huggingface_use_and_potential.md`](./huggingface_use_and_potential.md)**  
  Documents current use of Hugging Face (embeddings) and outlines a roadmap for integrating other HF pipelines (NER, QA, classification...).

---

## Data Science Intuition

- **[`data_science_involved.md`](./data_science_involved.md)**  
  A reflection on how classic data science skills (debugging filters, interpreting metadata failures, prompt evaluation, etc.) added value throughout the assistant's development.  
  This includes examples where structured reasoning, variable selection, or understanding model behavior went beyond default usage of LangChain.

---

## Purpose of This Folder

This archive is not meant to showcase production code — it's a curated set of learning artifacts:

- To serve as future reference for similar projects
- To document what worked (and what didn’t)
- To highlight how classical DS thinking complements GenAI tools

If you're building retrieval-based assistants, reasoning agents, or Streamlit+LLM tools, these notes may save you time — or inspire better design decisions.

