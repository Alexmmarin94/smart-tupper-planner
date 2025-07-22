# Debugging Long, Unfocused LLM Responses and Metadata Blindness in the Nutrition Assistant

## Context

In early versions of the assistant, the overall pipeline was technically correct:  
`(user query → filter extraction → document filtering → QA prompt generation)`.  

However, two major issues arose in practice:

1. The LLM often generated **very long, unfocused responses**.
2. The model seemed to **ignore important metadata fields** like `kcal`, `proteinas`, or dietary tags during its reasoning.

These behaviors made the assistant less useful and harder to trust, especially in edge cases.

---

## Issue 1: Long, Exhaustive Responses with No Prioritization

### What Was Happening

Despite correct filtering logic, the `qa_prompt` used to generate answers had **no instructions** about tone, length, or prioritization. The LLM often received up to **300 formatted dish documents**, each containing rich nutritional fields.

As a result, it tried to be "helpful" by listing too many dishes, including excessive detail, and failing to focus on the user’s goal.

### How It Was Diagnosed

- The fallback logic often passed **all_docs** to the LLM when no strict matches were found.
- Each document included full nutritional breakdowns (protein, kcal, fat, allergens...).
- The LLM defaulted to exhaustive listings due to the lack of prompt guidance.

### Fix: Rewrite the QA Prompt with Explicit Instructions

The `qa_prompt` was rewritten to:

- Be **brief and direct**
- **Prioritize** top 3–5 dishes based on user goals
- Avoid rephrasing the filters
- Skip redundant explanation

In addition, we sometimes **limited the input** to `formatted_docs[:50]` to reduce context size and implicitly guide the model to synthesize better.

### Result

- The LLM now behaves like a **focused assistant**, not a verbose catalog.
- Answers are clearer, more actionable, and tailored.
- The model shows improved alignment with user intent.

---

## Issue 2: LLM Ignored Metadata in Final Recommendations

### What Was Failing

Initially, we used a `SelfQueryRetriever` to filter dishes based on metadata fields like `sin_gluten`, `kcal`, or `para_diabeticos`.

After filtering, we passed the retrieved documents to a QA chain built with `create_stuff_documents_chain`. The expectation was that the LLM would consider both `page_content` and `metadata` when generating recommendations.

Instead, the model **ignored metadata entirely** — never mentioning protein, calories, or gluten tags.

### Diagnosis

We realized that:

- LangChain chains like `create_stuff_documents_chain` **only expose `page_content`** to the LLM.
- Metadata fields are **not visible** to the model unless explicitly rendered into text.

Once we appended a formatted metadata summary into each document’s `page_content`, the model began to reference those fields correctly.

---

## Fix: Inject Metadata Into page_content Before QA Step

We replaced the `SelfQueryRetriever` with a **manual two-step filtering system**:

1. The LLM + `JsonOutputParser` extracted filter constraints.
2. We filtered `all_docs` manually using `.metadata`.

Then, we **rebuilt each document’s `page_content`** to include a human-readable metadata summary:

```python
def format_doc(doc: Document) -> Document:
    meta = doc.metadata
    extras = "\n".join([
        f"- Kcal: {meta.get('kcal')}",
        f"- Proteins: {meta.get('proteinas')}",
        f"- Carbs: {meta.get('hidratos')}",
        f"- Fat: {meta.get('grasas')}",
        f"- Allergens: {meta.get('alergenos', 'Unknown')}",
        f"- Gluten-free: {meta.get('sin_gluten')}",
        f"- Vegetarian: {meta.get('is_vegetariano')}",
        # And more
    ])
    return Document(
        page_content=f"{doc.page_content}\n\n{extras}",
        metadata=meta
    )
```

---

## Takeaways

### Prompt design matters

- Always **guide the LLM** on tone, length, and intent — especially when passing large contexts.
- Set **hard constraints** like "max 3 results", "be concise", or "focus on X".

### Metadata is invisible by default

In LangChain:

- Metadata is great for **filtering before generation**
- But any information you want the LLM to reason about **must live in `page_content`**

Otherwise, it will behave as if that information does not exist.

---

## Summary

| Issue                            | Root Cause                                  | Fix                                                       |
|----------------------------------|---------------------------------------------|------------------------------------------------------------|
| LLM gave verbose, unfocused answers | No prompt control over style or scope       | Added concise QA instructions and result limits            |
| LLM ignored key nutritional fields | Metadata not visible to LLM                | Injected metadata into `page_content`                      |
| SelfQueryRetriever didn’t help     | Overhead and reduced flexibility           | Replaced with direct filter extraction and custom logic    |

These adjustments significantly improved answer quality, control, and alignment — making the assistant feel intelligent, not bloated.
