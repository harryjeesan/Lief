import os
import ast
import json
import logging

try:
    import esprima
except ImportError:
    esprima = None

logging.basicConfig(level=logging.INFO)

IGNORE_DIRS = {'.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build', '.next'}
MAX_LINES_PER_CHUNK = 150

def parse_python_file(filepath):
    blocks = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
            lines = source.splitlines()

        tree = ast.parse(source)

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno
                end_line = node.end_lineno
                
                # Failsafe: if block is huge, only take signature + docstring + first 20 lines
                code_lines = lines[start_line-1:end_line]
                if len(code_lines) > MAX_LINES_PER_CHUNK:
                    code_snippet = '\n'.join(code_lines[:20]) + '\n... (truncated due to length)'
                else:
                    code_snippet = '\n'.join(code_lines)

                blocks.append({
                    "name": node.name,
                    "type": type(node).__name__,
                    "file": filepath,
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": code_snippet
                })

    except Exception as e:
        logging.warning(f"Failed to parse Python file {filepath}: {e}")
        # Fallback to generic chunking
        blocks.extend(fallback_chunking(filepath))
    
    return blocks


def parse_js_file(filepath):
    blocks = []
    if not esprima:
        return fallback_chunking(filepath)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
            lines = source.splitlines()

        # Esprima might fail on JSX or TS, fallback is handled in except
        parsed = esprima.parseScript(source, {"loc": True, "jsx": True})
        
        for node in parsed.body:
            if node.type in ('FunctionDeclaration', 'ClassDeclaration'):
                name = node.id.name if node.id else "anonymous"
                start_line = node.loc.start.line
                end_line = node.loc.end.line
                
                code_lines = lines[start_line-1:end_line]
                if len(code_lines) > MAX_LINES_PER_CHUNK:
                    code_snippet = '\n'.join(code_lines[:20]) + '\n... (truncated due to length)'
                else:
                    code_snippet = '\n'.join(code_lines)

                blocks.append({
                    "name": name,
                    "type": node.type,
                    "file": filepath,
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": code_snippet
                })
            # Handle VariableDeclarations that are arrow functions
            elif node.type == 'VariableDeclaration':
                for decl in node.declarations:
                    if decl.init and decl.init.type in ('ArrowFunctionExpression', 'FunctionExpression'):
                        name = decl.id.name
                        start_line = node.loc.start.line
                        end_line = node.loc.end.line
                        
                        code_lines = lines[start_line-1:end_line]
                        if len(code_lines) > MAX_LINES_PER_CHUNK:
                            code_snippet = '\n'.join(code_lines[:20]) + '\n... (truncated due to length)'
                        else:
                            code_snippet = '\n'.join(code_lines)

                        blocks.append({
                            "name": name,
                            "type": "ArrowFunction",
                            "file": filepath,
                            "start_line": start_line,
                            "end_line": end_line,
                            "code": code_snippet
                        })

    except Exception as e:
        logging.warning(f"Esprima failed on {filepath} (likely TS/JSX). Using chunking. Error: {e}")
        blocks.extend(fallback_chunking(filepath))
        
    return blocks


def fallback_chunking(filepath):
    """If a file cannot be parsed, split it into 150-line chunks."""
    blocks = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i in range(0, len(lines), MAX_LINES_PER_CHUNK):
            chunk = lines[i:i + MAX_LINES_PER_CHUNK]
            blocks.append({
                "name": f"Chunk_{i//MAX_LINES_PER_CHUNK + 1}",
                "type": "FileChunk",
                "file": filepath,
                "start_line": i + 1,
                "end_line": i + len(chunk),
                "code": "".join(chunk)
            })
    except Exception as e:
        logging.error(f"Could not read {filepath}: {e}")
    return blocks


def read_codebase(root_dir):
    all_blocks = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude ignored directories
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith('.')]
        
        for file in filenames:
            filepath = os.path.join(dirpath, file)
            
            if file.endswith('.py'):
                all_blocks.extend(parse_python_file(filepath))
            elif file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                all_blocks.extend(parse_js_file(filepath))
            elif file.endswith(('.json', '.md', '.html', '.css', '.yml', '.yaml')):
                # Just chunk other text files we might care about
                all_blocks.extend(fallback_chunking(filepath))

    return all_blocks

if __name__ == "__main__":
    # Quick test
    test_dir = os.path.dirname(__file__)  # Pointing to the leif/ folder
    print(f"Scanning {test_dir}...")
    blocks = read_codebase(test_dir)
    print(f"Found {len(blocks)} blocks.")
    with open("reader_test_output.json", "w") as f:
        json.dump(blocks, f, indent=2)
