# Cognitive Limitations of Small Local AI Models

When building autonomous agents powered by small local models (e.g., 7B-8B parameter models like Qwen2.5-Coder), there are strict cognitive ceilings regarding abstract reasoning and workflow orchestration.

## The Draft-Edit-Publish Failure
A brilliant, human-like workflow is **Draft ➔ Edit ➔ Publish**:
1. The junior agent writes a low-quality draft.
2. The junior agent passes the draft to a senior Cloud AI for editing.
3. The junior agent publishes the final premium content.

While GPT-4 or Claude 3.5 Sonnet can easily orchestrate this, **small local models completely fail.**

### Why They Fail:
1. **Semantic Looping**: When instructed to "draft the initial content", the small model panics. Instead of using `file_write` to physically create the draft, it attempts to offload the cognitive burden by using `consult_copilot` to ask the Cloud AI to write the draft for it.
2. **Buffer Blindness**: Because the Cloud AI's response is saved to a buffer (to protect the small model's context window), the small model never "sees" the draft in its chat history. 
3. **The Trap**: The small model thinks, "I still haven't written the draft," so it asks the Cloud AI *again*. This creates an infinite loop of the small model asking the Cloud AI to write the draft, never seeing it, and asking again, until it hits an error limit and crashes.

## The Solution: Explicit Crutch Tools
To bypass this cognitive limit, you must provide **explicit, 1-step crutch tools** rather than abstract workflow instructions.

Instead of teaching the agent *how* to manage a premium writing workflow, give it a button that says:
`generate_premium_content: "Click this to have the Cloud AI write premium content to a buffer."`

This reduces the cognitive load from a complex 3-step reasoning task down to a simple 1-step trigger. The agent clicks the button, the buffer fills up, and the agent reads the buffer. 

**Rule of Thumb for Local Agents**: Replace complex reasoning rules in the system prompt with explicit, single-purpose tools.
