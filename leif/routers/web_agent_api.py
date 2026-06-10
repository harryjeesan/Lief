from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import urllib.request
import urllib.parse
import re

router = APIRouter()

class SearchRequest(BaseModel):
    query: str

class ReadUrlRequest(BaseModel):
    url: str

@router.post("/api/tools/search")
async def search_web(request: SearchRequest):
    """Simple web search tool using DuckDuckGo HTML"""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(request.query)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            results = []
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE)
            for i, snip in enumerate(snippets[:5]):
                clean_snip = re.sub(r'<[^>]+>', '', snip)
                results.append(f"[{i+1}] {clean_snip}")
            if not results:
                return {"result": "No search results found."}
            return {"result": "\n".join(results)}
    except Exception as e:
        return {"result": f"Search failed: {str(e)}"}

@router.post("/api/tools/read_url")
async def read_url(request: ReadUrlRequest):
    """Simple URL content reader that strips HTML"""
    try:
        req = urllib.request.Request(request.url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Remove scripts and styles
            text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', html, flags=re.IGNORECASE)
            text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', text, flags=re.IGNORECASE)
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            # Clean whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return {"content": text[:10000]} # Limit to 10k chars to save context window
    except Exception as e:
        return {"content": f"Failed to read URL: {str(e)}"}
