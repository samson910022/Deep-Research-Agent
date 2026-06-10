"""
URL/Evidence Verification Script for Phase 4.5.
Requires: pip install duckduckgo_search requests

Usage: Modify the 'queries' list, then run this script to fetch real URLs and verify their liveness (HTTP Status).
Note for Windows MSYS bash: Always enclose the script path in double quotes when executing via an absolute python path to prevent backslash stripping.

DOI Resolution Strategy:
1. Preferred: CrossRef API (https://api.crossref.org/works/{doi}) — direct, fast, no rate limits for moderate usage.
2. Fallback: DuckDuckGo search — used when the DOI cannot be resolved via Crossref (e.g., non-DOI queries).
"""
from duckduckgo_search import DDGS
import requests
import json
import sys

# Default timeout for HTTP requests (seconds).
# Redirect chains may take longer than a simple HEAD request, so we allow
# generous headroom. Pass `timeout=N` to verify_urls() to override.
DEFAULT_TIMEOUT = 10


def verify_doi(doi: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """
    Resolve a DOI via the Crossref API.
    Returns a dict with keys: 'doi', 'title', 'url', 'status'.
    Status is 'Verified Alive' on success (HTTP 200), else the HTTP status code string.
    This is the *preferred* method for DOI validation — it is direct, authoritative,
    and does not count toward DuckDuckGo rate limits.
    """
    url = f"https://api.crossref.org/works/{doi}"
    try:
        resp = requests.get(url, timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            data = resp.json()
            title = (data.get('message', {}).get('title') or ['Unknown'])[0]
            doi_url = f"https://doi.org/{doi}"
            return {'doi': doi, 'title': title, 'url': doi_url, 'status': 'Verified Alive'}
        else:
            return {'doi': doi, 'title': 'Unknown', 'url': f"https://doi.org/{doi}", 'status': str(resp.status_code)}
    except Exception as e:
        print(f"[WARN] verify_urls: Crossref DOI resolution for '{doi}' failed: {e}", file=sys.stderr)
        return {'doi': doi, 'title': 'Unknown', 'url': f"https://doi.org/{doi}", 'status': 'Failed'}


def verify_urls(queries, timeout: int = DEFAULT_TIMEOUT):
    """
    For each query string, attempt to find a live URL via DuckDuckGo search,
    then verify HTTP liveness.
    
    Parameters:
        queries: list of search query strings.
        timeout: HTTP request timeout in seconds (default 10).
                 Increase if dealing with slow redirect chains.
    """
    results = []
    with DDGS() as ddgs:
        for q in queries:
            try:
                # Fetch top 2-3 results to find at least one working link
                for r in ddgs.text(q, max_results=3):
                    url = r['href']
                    title = r['title']
                    try:
                        res = requests.get(
                            url, timeout=timeout,
                            headers={'User-Agent': 'Mozilla/5.0'}
                        )
                        status_code = res.status_code
                        if status_code < 400:
                            status = 'Verified Alive'
                        elif status_code == 403:
                            status = 'exists_restricted'
                        else:
                            status = str(status_code)
                    except Exception as e:
                        print(f"[WARN] verify_urls: HTTP check for '{url}' failed: {e}", file=sys.stderr)
                        status = 'Failed'

                    # 403 often means Cloudflare block but the link itself exists
                    if status in ('Verified Alive', 'exists_restricted'):
                        results.append({
                            'query': q, 'title': title,
                            'url': url, 'status': status
                        })
                        break  # Found a valid link, move to next query
            except Exception as e:
                print(f"[WARN] verify_urls: query '{q}' failed: {e}", file=sys.stderr)
                continue

    print('---JSON_START---')
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print('---JSON_END---')
    return results


if __name__ == "__main__":
    # Default placeholder, easily modified by the agent before execution
    queries = [
        "Example query 1",
        "Example query 2"
    ]
    verify_urls(queries)
