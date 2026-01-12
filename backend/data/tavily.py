import json
import urllib.request
from typing import Dict, List, Any


class TavilyClient:
    BASE_URL = "https://api.tavily.com"

    def __init__(self, api_key: str = ""):
        if not api_key:
            raise ValueError(
                "Tavily API key is required. Set TAVILY_API_KEY in your .env file. "
                "Get a key at: https://tavily.com"
            )
        self.api_key = api_key

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}/search"

        payload = json.dumps(
            {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": True,
            }
        ).encode("utf-8")

        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Oracle/1.0",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

                results = []
                for item in data.get("results", []):
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "content": item.get("content", ""),
                            "score": item.get("score", 0),
                            "source": f"Tavily: {item.get('url', '')}",
                        }
                    )

                return results

        except Exception as e:
            return [{"error": str(e), "source": "Tavily API"}]

    def search_news(self, topic: str, days: int = 7) -> List[Dict[str, Any]]:
        query = f"{topic} news last {days} days"
        return self.search(query, max_results=5)

    def search_macro_events(self) -> Dict[str, List[Dict]]:
        topics = {
            "fed_policy": "Federal Reserve monetary policy decision",
            "ecb_policy": "ECB European Central Bank policy",
            "china_economy": "China economic stimulus policy",
            "geopolitical": "geopolitical tensions markets impact",
        }

        results = {}
        for key, query in topics.items():
            results[key] = self.search(query, max_results=3)

        return results
