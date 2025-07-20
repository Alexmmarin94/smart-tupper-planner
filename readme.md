# Nococinomas Assistant

This repository contains the codebase for **Nococinomas Assistant**, a Spanish-language AI-powered dish recommender designed to help users of [nococinomas.es](https://www.nococinomas.es/) choose their weekly meals based on dietary constraints, ingredient preferences, and nutrition goals.

Although the interface and variable names are in English, **both the prompts and the expected input/output are in Spanish**. This is intentional: the original data (menu and ingredient list) is in Spanish, and so are user expectations. While it would have been possible to detect and translate languages using a `langdetect` + Transformers pipeline (e.g., translating from English to Spanish before querying the LLM and vice versa), this was intentionally not done. The app is intended for Spanish-speaking users (where the website delivers), and such machinery would add unnecessary complexity for this use case.

This project was created for **educational purposes and personal use**, as the author is a regular customer of Nococinomas and uses this assistant to plan weekly orders.

---

## What This Project Is (and Is Not)

- ❌ This is **not a chatbot**.  
- ✅ It is a **retrieval-based recommendation assistant** that interprets a question and returns relevant dishes.
- ✅ It includes advanced logic for filtering, fallback scoring, and auditing.
- ✅ It combines LLM reasoning and deterministic data science rules.

---

## Folder and File Structure


```
root/
│
├── app.py                      ← Streamlit front-end interface  
├── .env                        ← API keys and environment settings (OpenRouter)  
├── requirements.txt            ← All required packages  
│
├── chroma_db/                  ← Local vector DB (auto-generated on first run)  
│
├── data/  
│   ├── raw.html                ← Downloaded HTML menu from nococinomas.es  
│   └── df_final_official.csv   ← Final annotated dish dataset  
│
├── learnings/                  ← Reflections and lessons from a DS perspective  
│
├── utils/                      ← Modular utilities for backend logic  
│   ├── __init__.py  
│   ├── diet_agent.py           ← LLM agent + fallback logic  
│   ├── diet_rules.py           ← Heuristics and keyword rules for tagging/filtering  
│   ├── html_parser.py          ← HTML parsing and ingredient extraction  
│   └── openai_router_wrapper.py← OpenRouter-compatible wrapper for ChatOpenAI  
│
├── 00_download_and_inspect_html.ipynb   ← Downloads raw HTML and previews dish format  
├── 01_parse_menu.ipynb                  ← Parses dishes from HTML into structured rows  
├── 02_tag_menu_items.ipynb              ← Tags metadata via heuristics and LLM  
├── 03_build_vectorstore.ipynb           ← Builds vector DB using HuggingFace embeddings  
└── 04_tevaluating_assistang.ipynb       ← Evaluates alignment of assistant responses  
```


> Many scripts are implemented as notebooks rather than pure `.py` files because this is a **data science-first project**. Explorability, intermediate validations, and the ability to view outputs inline take priority during development, especially when constructing or validating tagging logic or embedding similarity.

---

## 🧠 Data Science Contributions and Highlights

This project reflects significant **data science thinking and engineering** beyond just using an LLM:

---

### 📓 Notebooks and What They Do

Many components are implemented as notebooks rather than scripts. This is **intentional**: they enable interactive debugging, rich visualization, and iterative logic refinement — all essential in real-world prototyping. Reusability is ensured by wrapping shared logic into utility modules.

| Notebook                     | Purpose                                                                 |
|-----------------------------|-------------------------------------------------------------------------|
| `00_download_and_inspect_html.ipynb` | Downloads and visually inspects the raw HTML menu from nococinomas.es.       |
| `01_parse_menu.ipynb`                | Parses dish names, ingredients, and nutrition info into a structured DataFrame. |
| `02_tag_menu_items.ipynb`           | Applies deterministic and LLM-based rules to tag dietary attributes and filters. |
| `03_build_vectorstore.ipynb`        | Creates a local Chroma vector DB embedding dish descriptions + tags.            |
| `04_evaluating_assistant.ipynb`     | Tests assistant’s filter alignment vs. expected logic using structured metrics. |

---

### 🧩 Intelligent System Design

#### 1. Filter Logic, Fallbacks, and Scoring

When the assistant can't infer high-confidence filters from a user prompt (e.g. vague or noisy queries), the system falls back to **rule-based tagging**. It searches dishes using keyword/tag matching and scores each candidate based on:

- **Boolean tag alignment** (e.g. `is_vegano`, `sin_gluten`)
- **Soft numerical thresholds** (e.g. kcal < 500, proteínas > 20g)
- **Penalty weights** for partial or inverse matches

This fallback scoring is **tunable**, **interpretable**, and **grounded in business logic**, unlike opaque LLM outputs. It ensures robustness even when the model underperforms.

#### 2. Heuristics + LLM = Best of Both Worlds

In `02_tag_menu_items.ipynb`, each dish is tagged via two parallel systems:

- **Heuristics**: Deterministic rules based on string matching and ingredient analysis
- **LLM agent**: Extraction of attributes via prompted reasoning

This hybrid system allows:

- **Validation of agent predictions**
- **Robustness fallback** when LLM fails
- **Business rule enforcement** via hardcoded overrides

#### 3. Personalization & Rule-Based Overrides

The tagging logic includes handcrafted features (e.g. `para_diabeticos`, `de_cuchara`) that go **beyond model inferences**. These are injected during preprocessing or fallback, allowing:

- Precise control over domain-specific labels
- Adaptability to future menu changes
- Elimination of hallucination risks by anchoring logic in real data

#### 4. Evaluation and Testing

The assistant isn’t evaluated with just precision/recall or BLEU-style matching.

In `04_evaluating_assistant.ipynb`, we evaluate **intent alignment**:

- The true expected filters from a user query are defined.
- The assistant’s inferred filters are parsed from its reasoning trace.
- Structural comparison is performed (e.g. tag sets, value ranges), enabling:

  - Detection of false positives/negatives
  - Bias or hallucination tracing
  - Debugging of ambiguous interpretations

This goes **beyond surface-level comparison** and aligns with how real-world assistants must be audited for business-critical workflows.

#### 5. Controlled Retrieval Pre-Fallback

Before triggering fallback logic, the vector search layer can be **pre-conditioned** with inferred metadata or semantic cues:

- `"económicos y saludables"` may prioritize `precio < 6€` and `bajo_en_calorias`
- `"gourmet vegano"` narrows to `is_vegano` and `is_gourmet`
- `"congelable para toda la semana"` expands the match to `congelar = True` and meal diversity

This allows **midway correction** and intelligent broadening or narrowing of the search, increasing relevance without requiring LLM re-prompting.
This kind of **interpretable, hybrid control** is key when deploying GenAI in production—and comes naturally from a data science mindset.

---

## Streamlit Deployment

The project includes a lightweight **Streamlit front-end** (`app.py`) to make the assistant accessible to non-technical users. The UI is intentionally simple and human-friendly, allowing anyone to:

- Ask dietary questions in natural language.
- Receive curated dish recommendations with reasoning.
- Debug unexpected results via structured fallbacks (optional in dev mode).

### Key Features of the UI

- **Real-time inference** with visual feedback and status messages.
- **Multilingual-friendly input**, adapted for Spanish dietary expressions.
- **Expandable examples** to guide user prompts.
- **Backend integration** via a modular `get_answer_to_question()` function.

The app is ideal for demoing or embedding into internal tools, and can be deployed via:

- Local execution (`streamlit run app.py`)
- Sharing via `Streamlit Community Cloud`
- Embedding in web portals (via iframe or wrapper)

---

### 🔗 Live Demo

You can test the live assistant here:  
**👉 [Nococinomas Assistant – Streamlit App]([https://your-deployment-url-here](https://smart-tupper-planner-kkqcctszrk9q2ymsjedc8t.streamlit.app/))**  
*(Replace with your actual deployment URL once available)*

---

### 🖼️ Visual Preview (In Case Demo is Unavailable)

In case the assistant becomes temporarily inaccessible — for example, if the current OpenAI API key runs out of credits — we include **screenshot previews** of the assistant’s functionality below.

Each screenshot will be accompanied by a **short description in English** to illustrate the input, reasoning, and output.

This ensures the project remains understandable and auditable even if the hosted version goes down.


---


# Summary

This assistant is not just a demo of LangChain or embeddings—it’s a **working example of integrating GenAI into a constrained, production-like scenario**, with structured logic, safety checks, testing mechanisms, and data science reasoning behind every step.

Use it, fork it, and feel free to adapt it to your own favorite food delivery site or recipe catalog.

---  
Made with 🧠 by a data scientist tired of scrolling menus on Sunday nights.

---

#  Environment Configuration (`.env`)

This project is configured to work with **[OpenRouter](https://openrouter.ai/)**, a multi-provider LLM gateway that can route requests to models from different providers such as OpenAI, Anthropic, Mistral, etc.

To run the assistant locally, you’ll need to create a `.env` file at the root of your project with the following fields:

```env
OPENROUTER_API_KEY=sk-or-v1-3c...            # Replace with your actual OpenRouter API key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4.1-mini                # You can change this to any model supported by OpenRouter
```
