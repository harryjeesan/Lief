# Codebase Intelligence Report

> **Target Directory:** `C:\Users\Harriy\Desktop\project\Lief\leif`

> **Total Files Analyzed:** `8`

> **Total Blocks Summarized:** `40`


This report contains a highly compressed semantic map of the codebase architecture.

---

## 📄 `api.py`

- **_rotate_key()** `FunctionDef`: This function rotates the current API key used by a client, recording the timestamp when it was exhausted. It then selects the next available key from a predefined list and updates the client with this new key.
- **_groq_generate()** `FunctionDef`: This function takes a list of content objects or a critic string, converts them into OpenAI-compatible messages for use with Groq's Llama 3.3 model, and returns a response object that mimics Gemini's text output. It handles the conversion of roles to Groq-friendly formats, truncates history to stay within the free tier limit, and uses a system prompt to provide context before the actual conversation begins.
- **generate_with_fallback()** `FunctionDef`: This function attempts to generate content using multiple models, including Gemini 2.5 Flash + Thinking Mode (Tier 1), Gemini 2.5 Flash Lite (Tier 2), Groq Llama 3.3 70B (Claude-level, Tier 3), and falls back to a GROQ model if all other tiers are exhausted.
- **ChatRequest** `ClassDef`: This class defines a request for sending messages in a chat application, including the message content and an optional conversation identifier.
- **ChatResponse** `ClassDef`: This class defines a response object for a chat API, including a string response and an optional conversation identifier.
- **ExecuteRequest** `ClassDef`: This class defines a request to execute a command. It includes a single field, `command`, which is expected to be a string.
- **BrowseRequest** `ClassDef`: This class defines a request for browsing scripts, with a required field `script` of type string.
- **get_local_status()** `AsyncFunctionDef`: This function checks the environment variables for local Ollama settings and returns a dictionary with the live health status of the inference server. It uses the `get_ollama_status` function to fetch the current status from the Ollama server. The result is then formatted into a JSON-like dictionary that includes whether the service is enabled, online status, model name, and available models.
- **get_key_status()** `AsyncFunctionDef`: This function retrieves the live health status of all API keys in a rotation pool, including when each was exhausted and how long until Google resets it. It calculates the next reset time based on Pacific Time (UTC-7 or UTC-8) and returns a list of dictionaries containing key details such as index, hint, status, exhaustion details, and remaining time until reset.
- **delete_conv()** `AsyncFunctionDef`: This function deletes a conversation and all its messages. It handles exceptions and returns a success message or an error response.
- **execute_command()** `AsyncFunctionDef`: This function executes a given command on Harry's operating system, ensuring it is only run when the user explicitly approves and runs the command in the React UI. It uses subprocess to run the command and captures its output, handling exceptions and timeouts to prevent infinite hangs. The result is returned as a JSON object containing the command's output or an error message.
- **execute_browse()** `AsyncFunctionDef`: This function executes a Playwright Python script inside a visible Chromium browser, injecting Leif's script into a robust boilerplate. It captures the output of the script and returns it to the caller. If the script execution times out, it closes the browser window for Harry to view the video.
- **get_conversations()** `AsyncFunctionDef`: This function retrieves all conversations from the database and returns them in a JSON format, sorted by their last activity.
- **new_conversation()** `AsyncFunctionDef`: This function creates a new conversation by calling `create_conversation()` and returns an object containing the conversation's ID and title.
- **remove_conversation()** `AsyncFunctionDef`: This function deletes a conversation by ID and returns a confirmation message.
- **get_conversation_messages()** `AsyncFunctionDef`: This function retrieves all messages from a specified conversation by calling `get_history` with the given conversation ID and returns them in a JSON format.
- **chat_endpoint()** `AsyncFunctionDef`: This function handles a chat request by processing the user's message and optional file, routing it to the appropriate AI model based on complexity and availability. It uses local inference for simple tasks, Gemini for more complex ones, and Groq for fallbacks. The response is saved in memory scoped to each conversation.

## 📄 `browser_utils.py`

- **get_simplified_dom()** `FunctionDef`: This function extracts visible interactive elements from a web page, formats them into a list, and includes the page title for context. It handles exceptions gracefully and returns an error message if something goes wrong.

## 📄 `chat.py`

- **load_api_key()** `FunctionDef`: This function loads the Gemini API key from an environment variable. If the key is not found or is "your_actual_key_goes_here", it prints a message and exits the program. Otherwise, it returns the loaded key.
- **create_client()** `FunctionDef`: This function configures a modern Google GenAI client using the provided API key.
- **print_leif()** `FunctionDef`: This function prints a formatted message from Leif, including a separator line before and after the message.
- **print_welcome()** `FunctionDef`: This function prints a startup banner with a title, version information, and instructions for interacting with the chatbot.
- **main()** `FunctionDef`: This Python script connects to Leif using a modern SDK, handles user input, and sends messages back to Leif. It includes error handling for connection issues and provides a simple way to exit the chat session.

## 📄 `codebase_compiler.py`

- **compile_intelligence_report()** `FunctionDef`: This function compiles a detailed intelligence report about the codebase located at `target_dir`, including summaries of each block, and saves it to `output_file`. It uses local AI for summarization and organizes the results by file. The compression ratio is calculated to assess the effectiveness of the report in reducing context size compared to the original codebase.

## 📄 `codebase_reader.py`

- **parse_python_file()** `FunctionDef`: This function reads a Python file, parses its AST, and extracts the names, types, locations, and snippets of all functions, classes, and methods. It handles exceptions by falling back to a simpler chunking method if parsing fails.
- **parse_js_file()** `FunctionDef`: This function reads a JavaScript file, parses it using Esprima, and extracts functions and arrow functions into chunks for further processing or analysis. If Esprima fails due to JSX or TypeScript syntax, it uses fallback chunking instead. The extracted code snippets are stored in a list of dictionaries, each containing details such as the name, type, file path, start line, end line, and code snippet.
- **fallback_chunking()** `FunctionDef`: This function reads a file, splits it into chunks of up to 150 lines each, and returns a list of dictionaries containing information about each chunk. If the file cannot be read, it logs an error message.
- **read_codebase()** `FunctionDef`: This function reads a directory and its subdirectories, parsing Python, JavaScript, TypeScript, and JSON files into blocks of code. It excludes certain directories and ignores files that start with a dot. Other text files are chunked into smaller pieces for further processing.

## 📄 `codebase_summarizer.py`

- **summarize_code_blocks()** `FunctionDef`: This function takes a list of code blocks, checks if Ollama is running, and then uses HTTP requests to summarize each block using the OpenAI Ollama model. It returns a list of dictionaries containing the original file name, type, and summary for each block.

## 📄 `database.py`

- **init_db()** `FunctionDef`: This function initializes the database by creating tables for conversations and messages. It also migrates old schema if necessary to ensure compatibility with existing data.
- **create_conversation()** `FunctionDef`: This function creates a new conversation in the database with an optional title and returns its unique ID.
- **list_conversations()** `FunctionDef`: This function retrieves all conversations from the database, including their titles, creation and update timestamps, and the number of messages they have received. It orders the results by the most recent activity (most recent update time).
- **rename_conversation()** `FunctionDef`: This function updates the title of a conversation in a SQLite database based on the provided conversation ID and new title.
- **delete_conversation()** `FunctionDef`: This function deletes a conversation and all its messages from the database. It connects to the SQLite database, executes SQL commands to delete the specified conversation and its associated messages, commits the changes, and then closes the connection.
- **save_message()** `FunctionDef`: This function saves a message to a SQLite database. It checks if a conversation ID is provided, and if not, it retrieves the most recent conversation from the database. It then inserts the message into the messages table with the corresponding conversation ID. If the sender is "user", it updates the title of the conversation based on the first user message content.
- **get_history()** `FunctionDef`: This function retrieves message history from a SQLite database for a given conversation ID or the most recent conversation. It returns two lists: one with messages formatted as React history objects and another with messages formatted as Gemini history objects.

## 📄 `local_llm.py`

- **is_ollama_running()** `FunctionDef`: This function checks if the Ollama server running locally is accessible on `localhost:11434`. It uses the `httpx` library to send a GET request to the health check endpoint and returns `True` if the response status code is 200, indicating that the server is up and running. If an exception occurs during the request, it returns `False`.
- **get_ollama_status()** `FunctionDef`: This function checks the status of an Ollama server by making a GET request to the `/api/local-status` endpoint. It returns a dictionary indicating whether the server is online and which models are available. If there's an error during the request, it returns a default offline status with no models listed.
- **query_local()** `FunctionDef`: This function sends a prompt to the local Ollama model and returns a structured result. It includes checks for response length, uncertainty signals, and unclosed code blocks to determine if escalation is needed. If any of these conditions are met, it triggers escalation to Gemini.
- **is_complex_task()** `FunctionDef`: This function checks if a given message appears to be complex by looking for specific keywords. If it finds any of these keywords, it returns `True`, indicating the task is likely complex and should be handled differently than simpler tasks.