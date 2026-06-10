# Leif System Architecture

Here is the complete visual architecture of the Leif System, including the new VS Code Extension integration, the web frontend, the FastAPI backend, and the multi-tier AI Brain.

```mermaid
flowchart TD
    %% Define Styles
    classDef userInterface fill:#1e1e1e,stroke:#00ffaa,stroke-width:2px,color:#fff;
    classDef backend fill:#2d2d2d,stroke:#ff6b6b,stroke-width:2px,color:#fff;
    classDef memory fill:#1e1e1e,stroke:#4dabf7,stroke-width:2px,color:#fff;
    classDef brain fill:#1e1e1e,stroke:#fcc419,stroke-width:2px,color:#fff;
    classDef tools fill:#2d2d2d,stroke:#a61e4d,stroke-width:2px,color:#fff;
    classDef external fill:#1e1e1e,stroke:#868e96,stroke-width:1px,stroke-dasharray: 5 5,color:#fff;

    %% Client Interfaces
    subgraph Clients ["💻 Client Interfaces"]
        UI["🌐 React Web UI\n(localhost:5173)\n- Agent Mode Feed\n- Approval Gates\n- Key Status Panel"]:::userInterface
        
        VS["⚙️ VS Code Extension\n(leif-vscode)\n- Sidebar Chat\n- Native Terminal Exec\n- Auto-Distillation"]:::userInterface
    end

    %% API Layer
    subgraph API ["⚡ FastAPI Backend (localhost:8000)"]
        Router{"HTTP / WebSocket\nRouter (api.py)"}:::backend
        AgentLoop["ReAct Agent Loop\n(agent.py)"]:::backend
    end

    %% Memory Layer
    subgraph MemoryLayer ["💾 Memory Subsystem"]
        SQLite[("SQLite\n(Session History)")]:::memory
        Chroma[("ChromaDB\n(Vector Memory)")]:::memory
        Index[("Project Index\n(Live File Tree)")]:::memory
    end

    %% AI Brain Layer
    subgraph Brain ["🧠 Multi-Tier Intelligence Router"]
        Tier0["Tier 0: Local LLM\n(Phi-3 Mini / Ollama)\nOffline & Free"]:::brain
        Tier1["Tier 1: Cloud Primary\n(Gemini 2.5 Flash)"]:::brain
        Tier2["Tier 2: Cloud Fallback\n(Gemini Flash Lite)"]:::brain
        Tier3["Tier 3: Open Source Fallback\n(Groq Llama 3.3 70B)"]:::brain
        Copilot["Native VS Code LM\n(Copilot Fallback)"]:::brain
    end

    %% Tool Suite
    subgraph ToolSuite ["🔧 Autonomous Tool Suite"]
        WebRetrieve["Web Retrieval API\n(DDG, StackOverflow, Docs)"]:::tools
        CodeAnalyzer["Code Analyzer\n(pylint, ESLint, tsc)"]:::tools
        Sandbox["Code Sandbox\n(subprocess exec)"]:::tools
        Debugger["Structured Debugger\n(Trace Parser)"]:::tools
        Browser["Visual Browser Subagent\n(Playwright Chromium)"]:::tools
        Terminal["Terminal Execution\n(Approval-Gated)"]:::tools
    end

    %% Data Flow
    UI <-->|"HTTP/SSE"| Router
    VS <-->|"HTTP"| Router
    VS .->|"Fallback API"| Copilot
    
    Router <--> AgentLoop
    
    AgentLoop <--> Brain
    Brain --> Tier0
    Brain --> Tier1
    Brain --> Tier2
    Brain --> Tier3
    
    AgentLoop <--> ToolSuite
    ToolSuite -.->|"Read/Write"| Workspace[("Harry's File System\n(D:\\Upwork_Projects)")]:::external
    
    AgentLoop <--> MemoryLayer
```

## System Components Breakdown

### 1. The Client Interfaces
- **React Web UI:** The primary glassmorphic dashboard running on Vite. It features a Generative UI that renders complex React components directly in the chat stream (e.g., Action Lists, Phase Grids) and includes manual approval gates for safety.
- **VS Code Extension (`leif-vscode`):** A newly added native extension that embeds Leif directly into the IDE. It features a native terminal executor, allowing Leif to run commands directly inside your editor. It also has a powerful fallback to VS Code's native Language Models (like Copilot) if the local/cloud APIs fail.

### 2. The FastAPI Backend (`api.py` & `agent.py`)
This is the core orchestrator. It manages the **ReAct (Reason + Act)** loop that you recently upgraded with strict Standard Operating Procedures (SOPs). It breaks down complex Upwork tasks, loops through thoughts and actions, and streams the results back to the clients via Server-Sent Events (SSE).

### 3. The Multi-Tier Brain (`llm_router.py` & `local_llm.py`)
Leif operates on a cascading fallback system to maximize offline capability and minimize cost:
1. **Tier 0:** Fine-tuned Phi-3 Mini running locally via Ollama. It knows your coding patterns and processes simple requests for free.
2. **Tier 1:** Gemini 2.5 Flash (Primary Cloud).
3. **Tier 2:** Gemini Flash Lite.
4. **Tier 3:** Groq Llama 3.3 70B (Fast, free backup if Gemini quota is exhausted).
5. **VS Code Native:** If the backend completely fails, the VS Code extension natively hooks into your active Copilot/VS Code language models to keep working.

### 4. The Autonomous Tool Suite
Instead of guessing, Leif uses deterministic tools:
- **Web Retrieval:** Scrapes real documentation (DuckDuckGo, PyPI, React docs) instead of hallucinating APIs.
- **Code Analyzer & Debugger:** Runs linters and parses stack traces to fix errors before you even see them.
- **Visual Browser Subagent:** Uses Playwright to physically navigate the web, skip ads, read DOM elements, and extract information visually.
- **Project Mapper:** Compresses massive codebases into 2KB indices so the LLM understands the whole project without overflowing its context window.

### 5. Memory Subsystem
- **SQLite:** Handles real-time conversation history.
- **ChromaDB:** A vector database that gives Leif "Semantic Recall" to remember design decisions or preferences you mentioned weeks ago.
- **Distillation Engine:** When Leif successfully finishes a task, the trajectory is saved to `distilled_trajectories.jsonl` to train future versions of her local Tier 0 model.
