import os
import glob
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

DOWNLOADS_DIR = r"C:\Users\Harriy\Downloads"
MODELFILE_PATH = r"scripts\Modelfile"

def find_latest_gguf():
    # Find all gguf files in downloads
    gguf_files = glob.glob(os.path.join(DOWNLOADS_DIR, "*.gguf"))
    if not gguf_files:
        return None
    
    # Sort by modification time (newest first)
    gguf_files.sort(key=os.path.getmtime, reverse=True)
    return gguf_files[0]

def create_modelfile(gguf_path):
    modelfile_content = f"""FROM "{gguf_path}"
SYSTEM "You are Leif, an autonomous commercial software development agent. You write clean, modular, production-ready code."
PARAMETER temperature 0.3
PARAMETER num_ctx 4096
"""
    with open(MODELFILE_PATH, "w") as f:
        f.write(modelfile_content)
    logging.info(f"Created Modelfile pointing to: {gguf_path}")

def load_into_ollama():
    logging.info("\nLoading model into Ollama... this might take a minute...")
    try:
        # Run ollama create
        result = subprocess.run(
            ["ollama", "create", "leif-local", "-f", MODELFILE_PATH],
            capture_output=True,
            text=True,
            check=True
        )
        logging.info("✅ Model 'leif-local' successfully created in Ollama!")
        logging.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error("❌ Failed to load model into Ollama:")
        logging.error(e.stderr)

if __name__ == "__main__":
    latest_gguf = find_latest_gguf()
    if not latest_gguf:
        logging.error("❌ Could not find any .gguf files in the Downloads folder.")
        logging.info("Please make sure the download has completely finished.")
    else:
        logging.info(f"Found recently downloaded model: {os.path.basename(latest_gguf)}")
        create_modelfile(latest_gguf)
        load_into_ollama()
