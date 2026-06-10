# Phase 7: Codebase Intelligence Sub-System

To allow Leif to understand massive client repositories on Upwork without crashing her context window, we are going to build the **3-Tool Pipeline** outlined in the Build Plan.

## Goal Description
Create a set of Python scripts that break down a large codebase, summarize every function using a fast, lightweight local AI model (`qwen2.5-coder:1.5b`), and compile a highly compressed "Intelligence Report" that Leif can easily read.

## Proposed Changes

### [NEW] `leif/codebase_reader.py` (Tool 1: The Reader)
- A script that recursively scans a target directory.
- It will use Python's built-in `ast` module to accurately break `.py` files down into exact functions and classes.
- It will use a fallback regex/chunking method to break down `.js`, `.jsx`, and `.tsx` files into logical blocks.
- **Output:** A list of code blocks with their file paths and line numbers.

### [NEW] Ollama Model Setup (The Summarizer Engine)
- We will configure the system to pull `qwen2.5-coder:1.5b`. This is an extremely fast, lightweight model built specifically for reading code. It will run in the background to generate the summaries.

### [NEW] `leif/codebase_summarizer.py` (Tool 2: The Understander)
- A script that takes the code blocks from Tool 1 and feeds them sequentially to the local `qwen2.5-coder` model.
- It will prompt the model to generate a strictly 1-2 sentence plain-English summary of what the code does.
- **Output:** A JSON mapping of `File -> Function Name -> Summary`.

### [NEW] `leif/codebase_compiler.py` (Tool 3: The Compiler)
- A script that aggregates all the tiny summaries from Tool 2.
- It will format them into a heavily compressed Markdown document (the "Codebase Intelligence Report").
- *Note:* We will save the ChromaDB vector embeddings for Phase 9 as planned, keeping this phase focused purely on the semantic map generation.

## Open Questions

1. To parse JavaScript/TypeScript files perfectly in Python, we can either use simple Regex (fast, no dependencies, but occasionally misses nested functions) or install a Python-to-JS parser library like `esprima` (highly accurate, but adds a dependency). For Upwork projects, I recommend `esprima` for accuracy. **Do you approve adding the `esprima` Python package?**
2. Generating summaries for a huge codebase can take a few minutes locally. **Do you want me to add a progress bar (using the `tqdm` package) so you can see the summary generation happening in real-time?**

## Verification Plan
1. Write the 3 tools.
2. Run the pipeline against a test folder (we can use Leif's own `leif/` backend folder as the test codebase!).
3. Verify that a `codebase_report.md` is generated successfully and perfectly summarizes the backend logic in a tiny filesize.
