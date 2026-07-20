"""
search.py
---------
Owns all interaction with the live web via DuckDuckGo Search. This keeps
"fresh knowledge" retrieval isolated from the vector DB ("historic
knowledge") retrieval, so each source can fail independently without
crashing the whole pipeline.
"""

from duckduckgo_search import DDGS


def get_live_news_context(sport_name: str, max_results: int = 3) -> str:
    """
    Searches the live web for recent news, tournament results, or events
    for the given sport. Returns a single joined text block of snippets,
    or a graceful fallback message if the search fails (e.g. rate limits,
    no internet access) so the rest of the app can keep running.
    """
    search_query = f"{sport_name} latest tournament results championship winners news 2026"
    retrieved_texts = []

    print(f"[search] Executing web search for: '{search_query}'...")
    try:
        with DDGS() as ddgs:
            results = ddgs.text(search_query, max_results=max_results)
            for index, r in enumerate(results, start=1):
                title = r.get("title", "No Title")
                snippet = r.get("body", "No Snippet Content Available")
                retrieved_texts.append(f"Web Source {index}: {title}\nSnippet: {snippet}")
    except Exception as e:
        print(f"[search] Web search fell back or failed: {e}")
        return "No recent search engine updates available due to system connectivity."

    if not retrieved_texts:
        return "No recent search engine updates were found for this query."

    return "\n\n".join(retrieved_texts)
