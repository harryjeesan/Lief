import os
import argparse
from leif.codebase_reader import read_codebase
from leif.codebase_summarizer import summarize_code_blocks
import logging

logging.basicConfig(level=logging.INFO)

def compile_intelligence_report(target_dir, output_file="codebase_report.md"):
    logging.info(f"Step 1/3: Scanning codebase at {target_dir}...")
    blocks = read_codebase(target_dir)
    
    if not blocks:
        logging.error("No code blocks found to summarize.")
        return False
        
    logging.info(f"Found {len(blocks)} code blocks.")
    
    logging.info(f"Step 2/3: Summarizing {len(blocks)} blocks using local AI...")
    summaries = summarize_code_blocks(blocks)
    
    if not summaries:
        logging.error("Summarization failed or returned empty.")
        return False

    logging.info(f"Step 3/3: Compiling report to {output_file}...")
    
    # Group by file
    file_map = {}
    for item in summaries:
        filepath = item['file']
        # Convert absolute path to relative for readability
        rel_path = os.path.relpath(filepath, target_dir)
        if rel_path not in file_map:
            file_map[rel_path] = []
        file_map[rel_path].append(item)
        
    # Generate Markdown
    md_content = [
        "# Codebase Intelligence Report\n",
        f"> **Target Directory:** `{target_dir}`\n",
        f"> **Total Files Analyzed:** `{len(file_map)}`\n",
        f"> **Total Blocks Summarized:** `{len(summaries)}`\n\n",
        "This report contains a highly compressed semantic map of the codebase architecture.\n",
        "---"
    ]
    
    for filepath, items in sorted(file_map.items()):
        md_content.append(f"\n## 📄 `{filepath}`\n")
        
        for item in items:
            name = item['name']
            type_str = item['type']
            summary = item['summary']
            
            # Format: - **function_name()** `[FunctionDef]`: This function does x.
            if 'Function' in type_str or type_str == 'ArrowFunction':
                display_name = f"{name}()"
            else:
                display_name = name
                
            md_content.append(f"- **{display_name}** `{type_str}`: {summary}")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
        
    logging.info(f"✅ Success! Report generated at {output_file}")
    
    # Print file size savings roughly
    raw_size = sum(len(b['code']) for b in blocks)
    report_size = os.path.getsize(output_file)
    compression = (1 - (report_size / raw_size)) * 100 if raw_size > 0 else 0
    logging.info(f"Compression Ratio: Raw {raw_size/1024:.1f}KB -> Report {report_size/1024:.1f}KB ({compression:.1f}% reduction in context size)")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile a codebase intelligence report.")
    parser.add_argument("target_dir", nargs="?", default=".", help="Directory to analyze")
    parser.add_argument("--out", default="codebase_report.md", help="Output markdown file")
    
    args = parser.parse_args()
    
    # Ensure it's an absolute path
    target = os.path.abspath(args.target_dir)
    compile_intelligence_report(target, args.out)
