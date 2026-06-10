# Code Review Report: Deep Research Agent

## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** This repository defines a sophisticated multi-phase scientific research pipeline with subagent orchestration, peer review, document generation, and knowledge base integration. The architectural ambition is commendable, but several critical correctness and reliability gaps — particularly around error handling, path hardening, SSL security, and unbounded iteration — must be resolved before this pipeline can be considered production-ready.

**Scope reviewed:**
| File | Lines |
|------|-------|
| `README.md` | Full |
| `skills/deep-science-writer/SKILL.md` | Full |
| `skills/deep-science-writer/references/academic-api-patterns.md` | Full |
| `skills/deep-science-writer/references/python-docx-manipulation.md` | Full |
| `skills/deep-science-writer/scripts/mermaid_to_png.py` | 33 |
| `skills/deep-science-writer/scripts/verify_urls.py` | 45 |
| `skills/remi/SKILL.md` | Full |

---

## Critical Issues

### C1. Hardcoded Username Path (Obsidian Vault) [skills/deep-science-writer/SKILL.md:28]

**Observation:** Phase 7 hardcodes `C:\Users\User\Documents\Obsidian Vault\Hermes\` with the literal username `User`. This will fail on every real Windows machine — the OS uses the actual account name (e.g., `samso`), not `User`.

**Risk:** The entire Phase 7 Obsidian update silently fails for every user, and because no error check is specified in the skill instructions, the agent may report completion without the knowledge base being updated.

**Fix:** Replace with an environment-variable-driven path:
```
C:\Users\%USERNAME%\Documents\Obsidian Vault\Hermes\
```
Or better, make the vault path a configurable variable in the skill frontmatter with a clear comment that users **must** update it. The README already mentions this (`Update SKILL.md Phase 7 if your vault is located elsewhere`) but the hardcoded `User` string is an obvious trap — defaulting to `User` practically guarantees failure.

---

### C2. Hardcoded `D:\` Drive with No Fallback [skills/deep-science-writer/SKILL.md:28]

**Observation:** Phase 6 unconditionally saves the final `.docx` to `D:\Research_Report.docx`. Many Windows laptops ship with a single `C:\` partition. On such systems, the write will throw an unhandled exception and the output is lost.

**Fix:** Define a fallback resolution order:
```
priority: 1. D:\  2. C:\Users\%USERNAME%\Documents\  3. environment variable OUTPUT_DIR
```
The README already warns users to adjust this, but a silent crash is a bad default. Make fallback explicit in the skill instructions.

---

### C3. SSL Verification Disabled in Academic API Patterns [references/academic-api-patterns.md:24-26]

**File:** `skills/deep-science-writer/references/academic-api-patterns.md`

```python
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
```

**Observation:** The OpenAlex query example disables both hostname checking and certificate verification. This exposes all DOI verification traffic to MITM attacks. An attacker on the same network could silently substitute fake DOI metadata, causing the anti-hallucination phase to validate fake citations against attacker-controlled responses.

**Risk:** Direct subversion of the **zero-hallucination guarantee** — the pipeline's most important quality claim.

**Fix:** Remove the two lines that override SSL verification. The default SSL context is sufficient for the OpenAlex API (which uses a valid commercial certificate). If certificate issues arise, document a targeted fix rather than blanket disabling:

```python
ctx = ssl.create_default_context()
# NOTE: Only disable hostname checking if behind a corporate MITM proxy
# ctx.check_hostname = False  # REMOVED
# ctx.verify_mode = ssl.CERT_NONE  # REMOVED
```

---

### C4. Silent `except pass` in URL Verification [scripts/verify_urls.py:27-28]

**File:** `skills/deep-science-writer/scripts/verify_urls.py`, lines 25-28

```python
except Exception as e:
    pass
```

**Observation:** The outer `try/except` wrapping the query loop silently swallows **every** exception. If `DDGS` (DuckDuckGo Search) is blocked, rate-limited, or the network is down, the function returns an empty results list with no warning. The agent proceeds to Phase 5 believing all citations verified.

**Risk:** Complete bypass of the anti-hallucination guarantee. Dead/fake citations pass through to the final manuscript.

**Fix:** At minimum, print the exception to stderr before continuing. Better: re-raise on unexpected errors and let the caller decide:

```python
except Exception as e:
    print(f"[WARN] verify_urls: query '{q}' failed: {e}", file=sys.stderr)
    continue
```

---

### C5. Unbounded Peer-Review Iteration Loop [skills/deep-science-writer/SKILL.md:Phase 5]

**Observation:** Phase 5 instructs: *"Repeat the Remi review process until Remi approves the manuscript with zero critical concerns."* There is no maximum iteration count, no timeout, no escalation path for a stuck loop.

**Risk:** If Remi consistently finds issues (due to prompt strictness or conflicting styles), the agent loops infinitely, exhausting the context window and/or API costs. This is a real failure mode with LLM-based reviewers.

**Fix:** Add a hard iteration cap (e.g., max 3 rounds). After the cap, surface the remaining Remi concerns as a "known limitations" section in the manuscript and proceed. Document the cap clearly:

```
### Phase 5: Peer Review & Iteration
...
4. **Maximum 3 review rounds.** If Remi still has concerns after round 3, document each unresolved concern as a "Limitations" subsection and proceed to Phase 6.
```

---

## Important Issues

### I1. 403 Status Mislabeled as "Verified Alive" [scripts/verify_urls.py:31]

**File:** `skills/deep-science-writer/scripts/verify_urls.py`, line 31

```python
if status == 'Verified Alive' or status == '403': 
    results.append({'query': q, 'title': title, 'url': url, 'status': 'Verified Alive'})
```

**Observation:** An HTTP 403 (Forbidden) response is treated identically to a 200 OK and labeled `'Verified Alive'`. A 403 from a DOI resolver (e.g., doi.org) typically means the DOI **exists** but access is restricted — this is usually acceptable. However, the label is misleading. More critically, the condition error-handles correctly for the `Failed` case but then maps `'403'` to `'Verified Alive'` only because the preceding `requests.get` stores the string `'403'` (from `str(res.status_code)`), and the code checks the string `'403'`, not the integer 403. This coincidental string comparison works, but it's fragile.

**Fix:** Make the intent explicit and use integer status codes:

```python
try:
    res = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
    if res.status_code < 400:
        status = 'alive'
    elif res.status_code == 403:
        status = 'exists_restricted'
    else:
        status = f'error_{res.status_code}'
except Exception as e:
    status = 'failed'

# Accept alive or exists_restricted
if status in ('alive', 'exists_restricted'):
    results.append({'query': q, 'title': title, 'url': url, 'status': status})
    break
```

---

### I2. In-Place List Modification While Iterating [references/python-docx-manipulation.md:38-40]

**File:** `skills/deep-science-writer/references/python-docx-manipulation.md`

```python
if start_idx != -1:
    for p in doc.paragraphs[start_idx:]:
        p._element.getparent().remove(p._element)
```

**Observation:** Iterating over `doc.paragraphs[start_idx:]` while simultaneously removing elements from the document's internal XML tree can produce subtle corruption. The `for p in ...` creates an iterator over the paragraph list, but `remove(p._element)` mutates the underlying tree structure. Python-docx may cache the paragraph list, but depending on the version, this may cause `lxml` to raise `ElementTree` exceptions or skip elements.

**Fix:** Collect elements first, then remove:

```python
if start_idx != -1:
    to_remove = [p._element for p in doc.paragraphs[start_idx:]]
    parent = to_remove[0].getparent()
    for elem in to_remove:
        parent.remove(elem)
```

---

### I3. Hard `sys.exit(1)` Prevents Graceful Degradation [scripts/mermaid_to_png.py:24]

**File:** `skills/deep-science-writer/scripts/mermaid_to_png.py`, line 24

```python
except Exception as e:
    print(f"Failed to generate Mermaid PNG: {e}")
    sys.exit(1)
```

**Observation:** In a multi-diagram pipeline, a single failed mermaid.ink request kills the entire process. The calling agent may not distinguish a `sys.exit(1)` from a Python error, losing the partial work.

**Fix:** Raise a custom exception instead of exiting. Let the caller decide whether to abort or continue:

```python
class MermaidGenerationError(Exception):
    pass

# In the function:
except Exception as e:
    raise MermaidGenerationError(f"Failed to generate Mermaid PNG: {e}") from e
```

Then in the calling code (Phase 6), document that the agent should catch `MermaidGenerationError`, log the failure, and continue with a textual fallback (or regenerate with a simpler diagram).

---

### I4. `ddgs` / `DDGS` Import Ambiguity [scripts/verify_urls.py:6]

**File:** `skills/deep-science-writer/scripts/verify_urls.py`, line 6

```python
from ddgs import DDGS
```

**Observation:** The `ddgs` package on PyPI is an **unofficial** third-party wrapper for DuckDuckGo Search. It is not the same as the well-maintained `duckduckgo_search` library (which also exports `DDGS`). The README's `pip install ddgs requests` installs the unofficial wrapper, which may break without notice when DuckDuckGo changes their HTML. The official library is `duckduckgo_search` (`pip install duckduckgo_search`).

**Fix:** Switch to the widely-adopted `duckduckgo_search` library and update the pip install instruction:

```
pip install duckduckgo_search requests
```

With the import:
```python
from duckduckgo_search import DDGS
```

---

### I5. No Rate-Limiting / Pagination Guidance for 700+ Paper Fetch [skills/deep-science-writer/SKILL.md:Phase 0.5]

**Observation:** The skill mandates 700+ papers per subagent but provides no code samples for pagination, rate-limit backoff, or concurrent fetch throttling. Scopus API limits are typically 5,000 requests per week for free tiers, with per-second rate limits. Fetching 700 paper records (at ~25 per page = 28 API calls) is feasible, but a subagent without explicit pagination logic will likely time out or hit rate limits.

**Risk:** The 700+ paper target is aspirational but underspecified. A subagent implementing this from scratch (as instructed) will likely produce fewer papers or time out.

**Fix:** Provide a concrete pagination template in the skill references:

```python
# Example: OpenAIRE / Scopus pagination pattern
def fetch_all_papers(query, per_page=25, max_pages=30):
    all_results = []
    for page in range(1, max_pages + 1):
        resp = requests.get(f"{BASE_URL}?query={query}&page={page}&per_page={per_page}",
                            headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            time.sleep(5)  # rate-limit backoff
            continue
        data = resp.json()
        all_results.extend(data.get('results', []))
        if len(data.get('results', [])) < per_page:
            break  # no more pages
        time.sleep(1)  # rate-limit courtesy
    return all_results
```

---

### I6. No Test Infrastructure

**Observation:** There are zero test files in the repository. The pipeline contains:
- Network-dependent scripts with no unit tests (`mermaid_to_png.py`, `verify_urls.py`)
- Complex orchestration logic (7 phases with subagent dispatch)
- Document manipulation code (Phase 6 python-docx)

Without tests, regressions are undetectable, and the "zero-hallucination guarantee" cannot be programmatically validated.

**Fix:** At minimum, add:
1. **Unit tests for `mermaid_to_png.py`** — mock `urllib.request.urlopen` and verify correct base64 encoding
2. **Unit tests for `verify_urls.py`** — mock `DDGS` and `requests.get` to verify state machine logic
3. An integration test placeholder that validates the pipeline end-to-end (or at least Phase 4.5 → Phase 6)

---

### I7. Missing Error Propagation from Failed Subagents [skills/deep-science-writer/SKILL.md:Phase 0.5]

**Observation:** If Subagent A (Scopus) fails or times out, there's no documented fallback. Subagent B runs independently, but Subagent C (Master Synthesizer) receives half the intended data. The pipeline has no circuit-breaker or partial-failure path.

**Fix:** Add a "Partial Failure Mode" subsection:

```
### Partial Failure Recovery
- If Subagent A fails: Subagent B should attempt to scale up to 1000+ papers to compensate.
- If Subagent B fails: The pipeline degrades to Scopus-only with a note in the manuscript.
- If both fail: Abort Phase 0.5 and present the failure to the user with diagnostic information.
```

---

## Suggestions

### S1. No Python Version Constraint in `requirements-style` Instructions

**File:** `README.md` and `skills/deep-science-writer/SKILL.md`

The pip install line (`pip install python-docx PyMuPDF requests matplotlib seaborn pandas`) does not pin versions. For a pipeline that may be run on different machines at different times, unpinned dependencies invite breakage when libraries release breaking changes (e.g., `matplotlib` 3.9 dropping APIs). Recommend adding a `requirements.txt` or at least documenting tested versions.

---

### S2. `mermaid_to_png.py` Hardcodes Theme as "default"

**File:** `skills/deep-science-writer/scripts/mermaid_to_png.py`, line 12-14

```python
"mermaid": {
    "theme": "default",
    "securityLevel": "loose"
}
```

Academic papers use a variety of visual styles. Making the theme configurable as a function parameter (with `"default"` as the fallback) would allow the agent to produce diagrams matching the document's visual theme. Also, `securityLevel: "loose"` permits HTML injection via diagram code — this is acceptable for locally-generated diagrams but worth a comment.

---

### S3. `verify_urls.py` — Make Timeout Configurable

**File:** `skills/deep-science-writer/scripts/verify_urls.py`

The 5-second timeout for `requests.get` is aggressive. DOIs resolving through redirect chains (e.g., `doi.org` → publisher → full-text) can take 5–10 seconds during peak hours. A configurable timeout parameter with a higher default (e.g., 10 seconds) would reduce false "Failed" statuses.

---

### S4. README License Section — "MIT" but No LICENSE File

**File:** `README.md` (last line)

The README states "License: MIT" but no `LICENSE` file exists in the repository. Without a license file, the default copyright laws apply (all rights reserved), which contradicts the MIT claim. Add `LICENSE` with the standard MIT license text.

---

### S5. `remi` Skill Numbering Skips 9

**File:** `skills/remi/SKILL.md`

The 10-point review framework lists items 1 through 8, then **8** again (Meta-commentary & Tone), then **10** (Final recommendation), then **11** (Improvement suggestions). Points 9 is missing and 8 is duplicated. This appears to be an editing error from a renumbering pass. The intent is clear but the inconsistency suggests the framework isn't well-maintained.

**Fix:** Renumber the list correctly from 1 to 10. The "Meta-commentary & Tone" item should be point 8, and "Major and minor issues" should be point 9.

---

### S6. "Action Over Planning" Contradicts Phase 0 Mandatory Halt

**File:** `skills/deep-science-writer/SKILL.md` — Pitfalls section vs Phase 0

The Pitfalls section says *"Action Over Planning: Do not tell the user what you **will** do. Immediately start executing..."* but Phase 0 explicitly says *"You MUST wait for the user's 'Explicit Approval' before proceeding."* These instructions are directly contradictory. Agents reading both will be confused about whether to halt for approval or proceed immediately. Recommend clarifying that Phase 0 (halt for approval) takes precedence, and remove or rephrase "Action Over Planning" to "Execute Decisively Once Approved."

---

### S7. Missing `.gitignore` for Generated Artifacts

No `.gitignore` exists in the repository. The pipeline generates:
- `.docx` files (Phase 6)
- PNG files in `assets/` (Phase 6)
- Potential CSV/JSON intermediate files (Phase 0.5)

Without a `.gitignore`, a user running the pipeline inside the repo will accidentally commit large generated files. Suggest adding:

```
*.docx
assets/
__pycache__/
*.pyc
*.egg-info/
```

---

### S8. Banned AI Vocabulary Could Be Machine-Readable

**File:** `skills/deep-science-writer/SKILL.md`, Phase 4

The banned vocabulary list is prose. For Phase 4.5 (automated scanning), providing the list in a machine-readable format (e.g., YAML list in the skill frontmatter or a separate `banned_vocab.txt`) would allow the agent to programmatically detect violations rather than relying on prompt awareness.

---

## What's Done Well

1. **Clear phase architecture.** The 7-phase breakdown with explicit responsibilities (Plan → Discover → Extract → Draft → Verify → Review → Compile → Integrate) is well-thought-out and easy to follow. Each phase has a distinct, measurable goal.

2. **Anti-hallucination is baked into the pipeline.** Phase 4.5 (DOI liveness + claim grounding) is a genuinely novel and valuable addition. Most research-sketch pipelines skip this entirely. The fact that it's mandated *before* peer review shows good workflow design.

3. **Dual-sourcing with subagents is ambitious and correct.** The idea of parallel Scopus + Open Access subagents feeding into a Master Synthesizer mirrors how real systematic reviews are done. The decoupling between discovery and synthesis is architecturally sound.

4. **DOI verification patterns are practical.** The `curl -I` / Crossref HEAD pattern in `references/academic-api-patterns.md` is exactly right — light, fast, and authoritative. The OpenAlex search pattern (with the URL encoding pitfall explicitly called out) shows domain experience.

5. **Remi's "no hallucinated citations" rule.** The most dangerous failure mode of LLM-based peer review is fabricating references that sound plausible but don't exist. Remi's explicit red line against this is excellent self-awareness.

6. **Pitfalls section is honest.** Calling out *"Action Over Planning"*, *"Paywalled Literature"*, and the Kroki vs mermaid.ink issue demonstrates real operational experience. These are exactly the kind of gotchas that sink novice implementations.

---

## Verification Story

| Check | Status | Observations |
|-------|--------|--------------|
| Tests reviewed | ❌ No | Zero test files in the repository |
| Build verified | ❌ N/A | No build/CI configuration found |
| Security checked | ⚠️ Partial | SSL disabled in reference patterns (C3); hardcoded paths (C1, C2); silent error suppression (C4) |
| Documentation reviewed | ✅ Yes | All 7 files read and analyzed |
| Scripts reviewed | ✅ Yes | Both Python scripts analyzed for correctness and edge cases |

---

## Summary of Findings

| Severity | Count |
|----------|-------|
| Critical | 5 |
| Important | 7 |
| Suggestion | 8 |
| **Total** | **20** |

**Bottom line:** The architectural design and workflow intent are strong. The practical implementation needs hardening in reliability (error handling, iteration limits, path fallbacks) and security (SSL verification, silent error masking) before this is safe to deploy in an automated research pipeline. The Critical issues (C1–C5) must be resolved before merge; the Important issues (I1–I7) should be addressed in the next development cycle.
