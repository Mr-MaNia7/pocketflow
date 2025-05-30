import os
from typing import List, Dict, Any
from firecrawl import FirecrawlApp


def search_web_firecrawl(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web using Firecrawl API.

    Args:
        query (str): The search query
        max_results (int): Maximum number of results to return (default: 5)

    Returns:
        List[Dict[str, str]]: List of search results with title, url, description, and markdown content
    """
    # Get API key from environment variable
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY environment variable not set")

    try:
        # Initialize Firecrawl app
        app = FirecrawlApp(api_key=api_key)

        # Search and scrape results
        search_result = app.search(query, limit=max_results)
        results = []

        for result in search_result.data:
            # Scrape each result URL
            scrape_result = app.scrape_url(
                result["url"], formats=["markdown"]  # Get clean markdown content
            )

            # Create result dictionary
            result_dict = {
                "title": result["title"],
                "url": result["url"],
                "description": result["description"],
                "data": scrape_result.markdown,
            }

            results.append(result_dict)

        return results

    except Exception as e:
        raise Exception(f"Error searching web: {str(e)}")


if __name__ == "__main__":
    # Example usage
    try:
        results = search_web_firecrawl(
            "Analyze the impact of AI on healthcare in the last 5 years", 1
        )
        print("\n=== Search Results ===\n")
        for result in results:
            print(f"Title: {result['title']}")
            print(f"URL: {result['url']}")
            print(f"Description: {result['description']}")
            print(
                f"Content: {result['data'][:200]}..."
            )  # Print first 200 chars of content
            print("\n---\n")
    except Exception as e:
        print(f"Error: {e}")
