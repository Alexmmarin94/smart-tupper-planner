# Metadata vs. Page Content in RAG Systems (Retrieval-Augmented Generation)

In any Retrieval-Augmented Generation (RAG) or QA pipeline, each document typically contains two key components:

- `page_content`: the **free-text content** passed to the LLM as **context** for answering the user's query.
- `metadata`: the **structured attributes** used to **filter relevant documents** before they’re retrieved.

---

## When to Use `metadata`

Use `metadata` when the field:

- Has a **structured format**: booleans, numbers, categories.
- Can be used for **exact or range-based filters** before retrieval.
- Doesn’t require linguistic interpretation.

Typical examples:

```json
{
  "sin_gluten": true,
  "kcal": 250,
  "is_vegano": false,
  "precio": 5.95
}
```

This enables queries like:

- “Show dishes with fewer than 400 kcal.”
- “Only include gluten-free desserts.”

---

## When to Use `page_content`

Use `page_content` for fields that:

- Are **free-form text** or unstructured.
- Provide **semantic context** the LLM needs to read.
- Contain information that benefits from **natural language understanding**.

Typical examples:

```text
ingredients: Water, Chicken 25%, Carrot, Garlic...
description: Ideal dish for people following a keto diet.
allergens: Dairy, Egg
```

These fields allow the model to **reason**, **interpret**, and generate more **accurate and natural responses**.

---

## Combined Benefits

Combining both elements leads to more powerful and efficient RAG systems:

| Component     | Purpose                          | Example                            |
|---------------|----------------------------------|------------------------------------|
| `metadata`    | Fast structured filtering        | `kcal < 400`, `sin_gluten = true` |
| `page_content`| Rich semantic context for the LLM| “high-protein and low-fat dish”    |

---

## Final Recommendation

> Use `metadata` for structured, machine-readable logic.  
> Use `page_content` to enrich the LLM's context with meaningful natural language.

A well-designed RAG system **leverages both layers** to achieve precision and depth in its responses.
