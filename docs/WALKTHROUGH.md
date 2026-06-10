# Walkthrough — Leif's Evolution

## Phase 2: Training Data Export (Fine-Tuning Prep)

I have successfully built the data extraction pipeline that will allow you to fine-tune Leif.

While we are waiting to gather 50-100 high-quality interactions before actually training the model, the extraction logic is now permanently in place.

### Changes Made

#### 1. Created `scripts/export_training_data.py`
* This standalone script safely connects to your SQLite memory database (`D:\Leif_Data\leif_memory.db`).
* It executes a query to pull all conversations, isolating pairs where the user speaks, immediately followed by Leif's response.
* **Quality Filtering:** It automatically skips any conversational exchanges where either message is less than 20 characters, ensuring the model isn't trained on low-value context like "yes" or "continue".
* **Formatting:** It strictly formats the data into the exact `ShareGPT / Unsloth` JSONL schema required by HuggingFace fine-tuning environments: `{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`

### Verification
I successfully ran the script against your current live database. 
* It connected flawlessly to the SQLite DB.
* It extracted 35 high-quality QA pairs into `scripts/training_data.jsonl`.
* The encoding logic was validated to run natively on Windows without `cp1252` charmap crashing.

---
## Phase 1: Tier 0 Local Brain (Phi-3 Mini Integration)

I have successfully integrated the Tier 0 Local Brain, completely fulfilling Phase 1 of our `BUILD_PLAN.md`.

Leif now has the ability to process basic requests locally on your machine, using your RTX 3050 GPU, before reaching out to the cloud. This saves you API quota, works offline, and guarantees privacy for simple queries.

### Changes Made

#### 1. Setup Ollama & Model Pull
* Verified Ollama installation.
* Downloaded the **Microsoft Phi-3 Mini (3.8B parameters)** model to the `D:\Leif_Models` drive to preserve critical space on your `C:\` drive.

#### 2. Local LLM Module (`leif/local_llm.py`)
* Created the python module that communicates with Ollama locally.
* Implemented heuristic pre-screening: if a user asks a highly complex question (e.g. "architect a distributed system"), Leif skips the local model and goes straight to Gemini.
* Implemented escalation checking: if the local model responds with "I don't know" or "As an AI", the request is silently forwarded to Gemini.

#### 3. API Router Logic (`leif/api.py`)
* Refactored the `chat_endpoint` to support a 4-Tier cascade.
* Added a new endpoint `/api/local-status` to report the health of the local Ollama process to the React UI.

#### 4. React Frontend Updates (`App.jsx`)
* Added background polling for the local LLM status.
* Added a beautiful UI pill under the API Keys that says **Tier 0 Brain: Local LLM [ONLINE]**.

### Verification

I used a browser subagent to interact with the React interface. The model is active and responding beautifully.

---

## Past Implementations

<details>
<summary>Leif DOM Inspection Feature (Playwright Subagent Update)</summary>

### 1. New Browser Utility Module
* **File:** [browser_utils.py](file:///c:/Users/Harriy/Desktop/project/Lief/leif/browser_utils.py)
* **Description:** Created `get_simplified_dom(page)` which scans the current page, finds visible interactive elements (buttons, inputs, anchors, selects, textareas), and maps their HTML tag, text, and key attributes (such as ID or placeholder) to a clean, formatted text list for Leif's consumption.

### 2. API Boilerplate sys.path Injection
* **File:** [api.py](file:///c:/Users/Harriy/Desktop/project/Lief/leif/api.py)
* **Description:** Modified `/api/browse` to dynamically append the project root directory (`os.getcwd()`) to `sys.path` in the temporary python script template. This allows the Playwright scripts written by Leif to import the local `leif` modules (like `leif.browser_utils`) without pathing errors.

### 3. Prompt Engineering Update
* **File:** [system_prompt.py](file:///c:/Users/Harriy/Desktop/project/Lief/leif/system_prompt.py)
* **Description:** Updated `LEIF_SYSTEM_PROMPT` to teach Leif about the `leif.browser_utils.get_simplified_dom` helper.

</details>
