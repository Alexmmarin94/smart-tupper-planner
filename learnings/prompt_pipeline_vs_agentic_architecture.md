# `filter_prompt + qa_prompt` vs. Agentic Architecture for Nutritional Recommendations

## Context

When building an intelligent assistant for dietary recommendations, two architectures can achieve the same functional goal:

- Interpreting user intent (e.g. _“vegan dishes under 400 kcal”_)
- Filtering a document corpus using metadata
- Returning a reasoned recommendation

But how you structure that logic — with a simple prompt chain or a full agent — greatly affects modularity, scalability, and traceability.

This note compares the two strategies used in the project:  
**prompt pipeline (`filter_prompt + qa_prompt`)** vs. **agent with tools**.

---

## Approach 1: `filter_prompt + qa_prompt` (Prompt-Based Pipeline)

A minimalistic but effective architecture using two prompts:

1. **`filter_prompt`** → Converts natural language into structured filters  
   _Example_: `{ sin_gluten: true, kcal: "<400" }`
2. **Filter logic (manual)** → Applies those filters over metadata
3. **`qa_prompt`** → Uses filtered documents to generate the final response

### ✅ Pros

- ✅ Simple and fast to implement
- ✅ Only 2 LLM calls (low cost/latency)
- ✅ Easy to debug
- ✅ Sufficient for well-defined, low-variance queries

### ❌ Cons

- ❌ Not modular — steps are tightly coupled
- ❌ Hard to extend — new logic requires manual changes
- ❌ No step-by-step reasoning trace
- ❌ Poor reusability of intermediate components

---

## Code Snapshot: Prompt-Based Version

```python
filters = extract_filters_via_prompt(user_query)  # e.g., with JsonOutputParser
filtered_docs = apply_filters(all_docs, filters)  # manual filter using doc.metadata
response = run_qa_prompt(filtered_docs)           # generate final answer
```

---

## Approach 2: Agentic Architecture with Tools

A more scalable architecture where the **LLM acts as a controller**, invoking tools as needed. Each logic block becomes a tool.

### Tools used in this project:

| Tool                    | Function                                                    |
|-------------------------|-------------------------------------------------------------|
| `extract_filters_tool`  | Extracts filters from text using LLM + parser               |
| `filter_documents_tool` | Filters documents based on metadata                         |
| `qa_response_tool`      | Generates final answer using `create_stuff_documents_chain` |

### Agent flow (dynamic):

```python
agent = initialize_agent(
    tools=[extract_filters_tool, filter_documents_tool, qa_response_tool],
    llm=ChatOpenRouter(),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

response = agent.run("Quiero platos sin gluten, vegetarianos y con más de 20g de proteínas")
```

---

### ✅ Pros

- ✅ Modular — each step is a reusable `Tool`
- ✅ Scalable — add/remove logic without rewriting pipeline
- ✅ Reasoning is traceable step-by-step
- ✅ Tools can be tested or deployed independently

### ❌ Cons

- ❌ More complex to implement and maintain
- ❌ 3+ LLM calls per run (higher cost)
- ❌ Requires clean tool descriptions and constraints

---

## Summary: When to Use What?

| Use Case                                       | Use `filter + qa_prompt` | Use Agent + Tools |
|------------------------------------------------|---------------------------|-------------------|
| Simple user intent                             | ✅                        |                   |
| Prioritize latency or cost                     | ✅                        |                   |
| Need for logic modularity                      |                           | ✅                |
| Expect to scale to more tools or logic steps   |                           | ✅                |
| Require auditability or explainability         |                           | ✅                |

---

## Conclusion

| Criteria              | Prompt-Based Pipeline       | Agent-Based Architecture          |
|-----------------------|-----------------------------|------------------------------------|
| Simplicity            | ✅ Very high                 | ❌ Requires design effort           |
| LLM Calls per Query   | ✅ 2                        | ❌ 3+                               |
| Scalability           | ❌ Low                      | ✅ High                             |
| Reusability           | ❌ Limited                  | ✅ Strong modularity                |
| Traceability          | ❌ Opaque                   | ✅ Step-by-step decision tracking   |
| Best Use Case         | Demos, stable flows         | Production assistants, extensible tools |

---

## Final Recommendation

- For **small, predictable flows**, `filter_prompt + qa_prompt` is ideal.
- For **flexible, multi-step assistants**, adopt an **agentic architecture** with well-defined tools.

You can start with the simpler approach and **refactor into tools** as the assistant grows in complexity.
