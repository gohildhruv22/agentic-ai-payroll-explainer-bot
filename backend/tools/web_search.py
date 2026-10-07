"""
Optional web/news search for compliance agent (SerpAPI or NewsAPI). Falls back to a stub if keys missing.
"""
import requests
from config import SERPAPI_KEY, NEWS_API_KEY


def web_search(query: str, search_type: str = "general") -> dict:
    if SERPAPI_KEY:
        result = _serp_search(query)
        if result["success"]:
            return result

    if NEWS_API_KEY:
        result = _news_search(query)
        if result["success"]:
            return result

    return {
        "success": True,
        "source": "fallback",
        "message": "Web search API keys not configured. Providing general knowledge response.",
        "results": [
            {
                "title": "API Keys Required",
                "snippet": (
                    "To get real-time tax and compliance updates, please configure "
                    "SERPAPI_KEY or NEWS_API_KEY in the .env file. The system will use "
                    "its built-in knowledge for now."
                ),
                "link": ""
            }
        ]
    }


def _serp_search(query: str) -> dict:
    try:
        params = {
            "engine": "google",
            "q": query + " India tax compliance 2025 2026",
            "api_key": SERPAPI_KEY,
            "num": 5,
        }
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get("organic_results", [])[:5]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", ""),
                })
            return {"success": True, "source": "serpapi", "results": results}
        return {"success": False, "error": f"SERP API returned {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _news_search(query: str) -> dict:
    try:
        params = {
            "q": query + " India payroll tax",
            "apiKey": NEWS_API_KEY,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 5,
        }
        response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = []
            for article in data.get("articles", [])[:5]:
                results.append({
                    "title": article.get("title", ""),
                    "snippet": article.get("description", ""),
                    "link": article.get("url", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "published": article.get("publishedAt", ""),
                })
            return {"success": True, "source": "newsapi", "results": results}
        return {"success": False, "error": f"News API returned {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
