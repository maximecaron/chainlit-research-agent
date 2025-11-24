from ddgs import DDGS
from typing import Any, Dict, List

def search_web(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    results = DDGS().text(query, max_results=num_results)
    # Convert results to a string
    results: List[Dict[str, Any]] = []
    for item in results:
        results.append(
            {
                "title": item.get("title"),
                "url": item.get("href"),
                "snippet": item.get("body"),
            }
        )
    return results