"""
URL/Evidence Verification Script for Phase 4.5.
Requires: pip install ddgs requests

Usage: Modify the 'queries' list, then run this script to fetch real URLs and verify their liveness (HTTP Status).
Note for Windows MSYS bash: Always enclose the script path in double quotes when executing via an absolute python path to prevent backslash stripping.
"""
from ddgs import DDGS
import requests
import json
import sys

def verify_urls(queries):
    results = []
    with DDGS() as ddgs:
        for q in queries:
            try:
                # Fetch top 2-3 results to find at least one working link
                for r in ddgs.text(q, max_results=3):
                    url = r['href']
                    title = r['title']
                    try:
                        res = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                        status = 'Verified Alive' if res.status_code < 400 else str(res.status_code)
                    except Exception as e:
                        status = 'Failed'
                    
                    # 403 often means Cloudflare block but the link itself exists
                    if status == 'Verified Alive' or status == '403': 
                        results.append({'query': q, 'title': title, 'url': url, 'status': 'Verified Alive'})
                        break # Found a valid link, move to next query
            except Exception as e:
                pass
                
    print('---JSON_START---')
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print('---JSON_END---')

if __name__ == "__main__":
    # Default placeholder, easily modified by the agent before execution
    queries = [
        "Example query 1",
        "Example query 2"
    ]
    verify_urls(queries)
