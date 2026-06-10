# [Goal Description]

Equip Leif with Web Search and Browsing capabilities so she can autonomously read up-to-date documentation, API references, and stack overflow solutions while building freelance web applications. This is critical for Upwork tasks involving external APIs or specific UI libraries.

## User Review Required

> [!TIP]
> This upgrade will make Leif truly independent. Instead of guessing how an API works or relying on outdated knowledge, she will Google it and read the docs herself! 

## Open Questions

None. The chosen packages (`duckduckgo-search` and `beautifulsoup4`) are fast, offline-compatible, and require no API keys or accounts.

## Proposed Changes

### Dependencies
- Run `pip install duckduckgo-search beautifulsoup4` to add the search engine and HTML parser.

### `leif/agent.py`

- **[MODIFY] System Prompt**:
  - Add `search_web` tool: `args: {"query": "search term"}`. Instruct her to use it to find documentation or examples.
  - Add `read_url` tool: `args: {"url": "https://..."}`. Instruct her to use it to read the content of URLs found in her searches.

- **[MODIFY] `execute_tool()` logic**:
  - Implement `search_web`: Use the `DDGS()` engine to perform a search and return the top 5 results (Title, URL, Snippet) formatted as JSON.
  - Implement `read_url`: Use `httpx` to fetch the raw HTML, and `BeautifulSoup` to strip out all the messy tags, returning pure readable text. To protect her context window, the text will be safely truncated if the webpage is massively long.

## Verification Plan

### Automated Tests
- N/A

### Manual Verification
1. Open Agent Mode and ask Leif: `"Use your search tool to look up the latest version of React, and read the first URL you find. Tell me what it says."`
2. Verify that she successfully executes `search_web`, finds a link, and executes `read_url` to read it.
