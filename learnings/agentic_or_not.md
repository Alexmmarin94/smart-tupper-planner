# Agentic or not: Evaluating the Architecture of the Assistant

## Context

The assistant was designed to help Spanish-speaking users of [nococinomas.es](https://www.nococinomas.es/) plan weekly meals based on dietary constraints and nutritional goals. It works by:

- Extracting constraints from a free-text query using `filter_prompt`
- Filtering dishes in a local vectorstore according to the inferred filters
- Generating a final recommendation using `qa_prompt`

This system is modular and performs well — but is it "agentic"? And does that even matter?

---

## Why This Is Not Technically an Agent

Although the system involves multiple reasoning steps, it is **not an agent in the strict sense**. It lacks:

- Autonomous decision-making about what steps to take
- Dynamic tool selection
- Iterative reasoning or flow control based on previous outcomes

Instead, it is a **deterministic pipeline**: the execution sequence (filter → filter documents → generate response) is fixed, and the LLM follows a predefined role in each step.

---

## What Would an Actual Agent Look Like?

A proper agent (e.g., in LangChain or LangGraph) typically involves:

- An LLM acting as a planner
- Several tools (with registered names, inputs, and outputs)
- A dynamic control loop where the LLM decides which tool to use at each step
- The ability to revise, retry, or adapt its approach

**Example of a potential agent:**

1. `extract_filters_tool`: extracts structured constraints like `{ sin_gluten: true, kcal: "<400" }`
2. `filter_documents_tool`: filters dishes based on those constraints
3. `qa_response_tool`: crafts a final recommendation

This orchestration could be handled by a ReAct agent or OpenAI Functions-based executor.

---

## What About `classify_dish(...)`?

The `classify_dish(...)` function — which classifies individual dishes using a prompt-based reasoning chain — **does resemble a micro-agent**:

- It has a clear task
- Applies structured reasoning logic
- Produces interpretable output
- Operates autonomously on a constrained input

It’s not wrapped in a formal tool interface, but conceptually it behaves like a standalone unit with agency over a single dish.

---

## Does This Distinction Matter?

**Not necessarily.**

The current solution is:

- Modular
- Efficient
- Easy to test
- Fit-for-purpose

Whether it's “agentic” is **a semantic distinction**, not a reflection of its effectiveness.

---

## Advantages of Not Using Agents

- Total control over execution flow
- Lower latency and token usage
- Fewer failure points (no planner, no multi-turn coordination)
- Easier to debug, maintain, and evolve

In real-world constrained environments (e.g. dietary tools, personal planners), this deterministic structure often outperforms more complex alternatives.

---

## When to Consider Going Agentic

You might want to switch to an agentic architecture if:

- User queries require multiple reasoning steps 
- You need dynamic fallback or retries based on context
- You want the model to select or chain tools based on user intent
- You’re building for open-ended general queries where rigid pipelines fall short

---

## Why Prompt-Based Filtering Is Not Truly a "Decision"

It may feel like the LLM is making decisions when it parses user intent and outputs filters. But this is **not agentic behavior**, because:

- The LLM is performing a **single static task**, as instructed by the prompt
- What happens next is **fully defined by the developer** — not decided by the model
- There is **no opportunity for adaptive strategy or branching logic**

The model doesn’t decide *whether* to filter, *how* to filter differently, or *how to proceed next* — it simply outputs structured filters that get applied by deterministic code.

---

## What Would a Real Decision Look Like?

In an agentic system, the model would **decide what to do next** based on intermediate results. For example:

**User input:**  
_"What dishes are high in protein but also safe for diabetics?"_

**Agentic flow:**

1. Use `filter_tool` with `{ high_protein: true }`
2. Use `lookup_ingredient` to check glycemic impact
3. If too few results are found:
   - Choose to relax constraints or rerun filter
4. Use `sort_tool` to rank by protein content
5. Call `qa_response_tool` to generate a final message

This decision tree is **not hardcoded** — (as in our case) it is built by the model as it goes, based on results and logic.

---

## Comparison Table: Deterministic vs. Agentic

| Feature                        | Prompt-Based Pipeline     | Agentic System            |
|-------------------------------|---------------------------|---------------------------|
| Tool selection                | ❌ Fixed                  | ✅ Dynamic                |
| Execution order               | ❌ Predefined             | ✅ Adaptive               |
| Handles retries/failures      | ❌ No                     | ✅ Yes                   |
| Can revise strategy           | ❌ No                     | ✅ Yes                   |
| Developer controls execution  | ✅ Fully                  | ⚠️ Partial                |
| Computation cost              | ✅ Minimal                | ❌ Higher (tokens, logic) |

---

## Conclusion

Your assistant is a **deterministic, modular pipeline**, not an agent — and that’s totally fine.

It is:

- Easier to test
- Faster and cheaper to run
- Aligned with a specific user task
- Built with solid engineering and reasoning

Labeling it as "agentic" might be misleading, but doesn’t detract from its value.

If future requirements demand more flexibility or autonomy, this architecture can evolve into an agentic one — using `LangChain AgentExecutor`, `LangGraph`, or `OpenAI Functions`.

For now, you’ve struck the right balance between control, cost, and clarity.
