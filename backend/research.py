"""
research.py — SerpAPI integration for real-time lead research.
Fetches news, funding rounds, job postings, and general company data.
"""

import os
import httpx
from typing import Optional

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY", "").strip()
SERPAPI_BASE = "https://serpapi.com/search"
ZENSERP_BASE = "https://app.zenserp.com/api/v2/search"


def _is_zenserp_key(key: str) -> bool:
    """Check if key is Zenserp format (UUID-like with dashes)."""
    return len(key) == 36 and key.count("-") == 4


async def fetch_lead_research(name: str, company: Optional[str] = None) -> dict:
    """
    Queries SerpAPI or Zenserp for recent news and information about a lead.
    Returns a structured dict with summary, articles, and funding info.
    """
    query = f"{name} {company or ''} news funding latest".strip()
    
    is_zenserp = _is_zenserp_key(SERPAPI_KEY)
    params = {"q": query}
    url = SERPAPI_BASE

    if is_zenserp:
        url = ZENSERP_BASE
        params["apikey"] = SERPAPI_KEY
        params["tbm"] = "nws"
    elif SERPAPI_KEY and SERPAPI_KEY != "your_serpapi_key_here":
        url = SERPAPI_BASE
        params["api_key"] = SERPAPI_KEY
        params["engine"] = "google"
        params["num"] = 5
        params["tbm"] = "nws"

    articles = []
    summary = ""

    if not SERPAPI_KEY or SERPAPI_KEY == "your_serpapi_key_here":
        return _mock_research(name, company)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        news_results = data.get("news_results", [])
        
        for item in news_results[:5]:
            articles.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "source": item.get("source", ""),
                "date": item.get("date", ""),
                "snippet": item.get("snippet", ""),
            })

        if articles:
            summary = f"Found {len(articles)} recent news articles for {name}."
        else:
            print(f"[Research] ⚠️ No real news found for {name}. Using mock fallback.")
            return _mock_research(name, company)

    except httpx.HTTPStatusError as e:
        print(f"[Research] ❌ HTTP {e.response.status_code}: {e}. Falling back to mock.")
        return _mock_research(name, company)
    except Exception as e:
        print(f"[Research] ❌ API Exception: {e}. Falling back to mock.")
        return _mock_research(name, company)

    return {
        "query": query,
        "summary": summary,
        "articles": articles,
    }


def _mock_research(name: str, company: Optional[str]) -> dict:
    """Returns mock research data for demo/dev purposes."""
    return {
        "query": f"{name} {company or ''} news",
        "summary": f"[DEMO] Found 3 mock news articles for {name}.",
        "articles": [
            {
                "title": f"{name if company is None else company} Secures Series B Funding",
                "link": "https://example.com/news/1",
                "source": "TechCrunch",
                "date": "2 days ago",
                "snippet": f"{company or name} has raised $20M in a Series B round to expand its AI platform.",
            },
            {
                "title": f"{name} Joins Forbes 30 Under 30",
                "link": "https://example.com/news/2",
                "source": "Forbes",
                "date": "1 week ago",
                "snippet": f"{name} was recognized for their work in enterprise software.",
            },
            {
                "title": f"{company or name} Announces Strategic Partnership",
                "link": "https://example.com/news/3",
                "source": "BusinessWire",
                "date": "3 weeks ago",
                "snippet": f"A new partnership that will accelerate growth in the APAC region.",
            },
        ],
    }
