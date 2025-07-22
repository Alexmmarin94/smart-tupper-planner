# `filter_prompt` vs. `qa_prompt`: Why Use Two Separate Prompts?

In this assistant, we use **two distinct prompts** to handle two very different tasks:

---

## What Is `filter_prompt`?

This prompt is designed to **interpret the user's query** and translate it into **structured filtering criteria**.

### Input:
Example query:  
> "I want vegetarian options that are gluten-free and under 400 kcal"

### Expected Output:
A JSON object such as:

```json
{
  "sin_gluten": true,
  "is_vegetariano": true,
  "kcal": "<400"
}
```

### Why Do This?

Because it allows us to **filter documents before passing them to the LLM**, using structured metadata (booleans, numerics, tags, etc.).  
This greatly improves relevance and reduces cognitive load on the model.

---

## What Is `qa_prompt`?

This is the prompt that **generates the final response** for the user, using:

- The original user question
- The filtered list of documents
- A natural language task description, e.g.:  
  _“You are a nutritionist. Recommend the most suitable dishes based on the following context...”_

---

## How Many LLM Calls?

**Two. Always.**

1. `filter_prompt` → interpret and generate filters  
2. `qa_prompt` → generate final output from filtered documents

This means **the token cost doubles** compared to a single-prompt pipeline.

---

## Advantages of Using `filter_prompt`

| Benefit                     | Why It Matters                                                                 |
|-----------------------------|--------------------------------------------------------------------------------|
| 🧠 Better accuracy           | Only relevant documents reach the LLM                                          |
| ⚙️ Clear separation of logic | You extract intent first, then generate — more interpretable                   |
| 📊 Reusable filters         | The structured output can be used in dashboards, analytics, audit logs         |
| 🧪 More control              | You can debug filter logic and response logic independently                    |

---

## Downsides

| Drawback               | Consideration                                                                     |
|------------------------|------------------------------------------------------------------------------------|
| 💰 Double token cost   | Two LLM calls per user interaction                                                 |
| 🐌 Slightly more delay | Small latency increase, usually imperceptible in UX                               |

---

## Alternatives

### Option 1: Only `qa_prompt` (No Pre-Filtering)

Just send the full user input and all documents into a single prompt. Let the model figure it out.

**✅ Pros**
- Only one call → cheaper and faster

**❌ Cons**
- Higher noise and irrelevant info
- No reuse of filters
- Harder to trace why certain dishes were chosen or omitted

---

### Option 2: Agent with Tools (`LangChain Agent`)

Instead of prompting linearly, use an agent where the LLM decides:
- First: extract filters
- Then: apply filters
- Finally: generate an answer

**✅ Pros**
- Fully modular and extensible
- Tools can be reused and tested in isolation

**❌ Cons**
- Higher setup complexity
- Higher LLM cost due to multiple steps

---

## Conclusion

Using `filter_prompt + qa_prompt` introduces **additional cost**, but in return gives:

- 🔬 Better reasoning and context control
- 🎯 More accurate, focused responses
- 🧱 A robust, extensible architecture

This design is ideal when quality, modularity, and future-proofing are priorities — especially for real users or production scenarios.
