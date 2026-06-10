# Known Limitations & Future Roadmap

This document tracks known limitations in Leif's current architecture and maps out the future upgrades required to solve them.

## 1. Local Agent Loop (Grammar Enforcement)
**Current Limitation:**
The autonomous ReAct Agent Loop exclusively uses Gemini 2.5 Flash. The local fine-tuned Phi-3 model is only used for Conversational Mode. This is because small local models often hallucinate JSON syntax, causing the autonomous loop to crash.

**Future Solution:**
Implement **Structured Grammar Enforcement** (via Ollama's `format="json"` API) natively in `leif/agent.py`. By forcing the first key of the JSON to be a `"thought"` string, the local model can calculate its logic while the API mathematically enforces perfect JSON syntax. 
*Next-Gen Hybrid Upgrade:* Once the local model enforces perfect JSON syntax to draft the action, we pass the draft to Gemini acting as a "Critic". Gemini verifies the logic using very few tokens, achieving world-class intelligence with near-zero API cost.

## 2. Context Window Limits
**Current Limitation:**
As conversations grow, the history passed to Gemini/Groq gets larger. If the context window exceeds the free tier limits (Groq is limited to 12,000 tokens per minute), the API will reject the request.

**Future Solution:**
We currently mitigate this by keeping only the last 8 messages for Groq. The ultimate solution is to implement a **Rolling Summary** system. When a conversation hits 10 messages, Leif automatically generates a dense summary of the first 5 messages, deletes them from the immediate context array, and injects the summary.

## 3. Browser Subagent Visibility
**Current Limitation:**
The Playwright Browser Subagent currently launches with `headless=False` so the user can watch the macro execute on their screen. This means the user cannot use their computer while the macro takes control of the mouse/keyboard.

**Future Solution:**
Implement a background headless browser that records its actions to a hidden virtual frame buffer (Xvfb) and streams a compressed WebP video directly into the React UI feed, allowing Leif to browse the web silently in the background.

## 4. API Key Exhaustion Polling
**Current Limitation:**
Leif waits until an API request fails with a `429 Too Many Requests` error before rotating to the next API key in the pool. This causes a minor 1-2 second latency spike during the failover.

**Future Solution:**
Implement a predictive token counter. Leif should count the tokens sent/received and preemptively rotate the key *before* hitting the quota wall to ensure zero latency spikes.
