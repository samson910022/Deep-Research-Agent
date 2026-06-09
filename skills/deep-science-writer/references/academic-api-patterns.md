# Academic API Query Patterns (Crossref & OpenAlex)

During Phase 4.5 (Anti-Hallucination), use these specific patterns to verify DOIs and retrieve metadata.

## 1. Crossref DOI Liveness Check (Terminal/Curl)
The fastest way to verify if a DOI exists is a silent HTTP HEAD request to the Crossref API.
```bash
# Returns HTTP 200 OK for real DOIs, HTTP 404 for hallucinations
curl -I -s https://api.crossref.org/works/10.1016/j.jclepro.2024.140123 | grep HTTP
```

## 2. OpenAlex Database Search (Python)
When searching OpenAlex for semantic matches (e.g., CBAM + AHP), use `urllib` but **beware of control character errors**. 

**PITFALL:** `urllib.request.urlopen` will throw `URL can't contain control characters` if the query contains spaces or quotes. You MUST use `urllib.parse.quote()` for the search string.

```python
import urllib.request
import urllib.parse
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# CORRECT: Quote the query string
query = '"Carbon Border Adjustment Mechanism" AHP MCDA'
url = 'https://api.openalex.org/works?search=' + urllib.parse.quote(query) + '&per-page=10'

req = urllib.request.Request(url, headers={'User-Agent': 'mailto:your.email@example.com'})
with urllib.request.urlopen(req, context=ctx) as response:
    data = json.loads(response.read().decode())
    for w in data.get('results', []):
        print(f"{w.get('title')} | DOI: {w.get('doi')}")
```