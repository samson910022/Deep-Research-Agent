---
name: deep-science-writer
description: "End-to-end scientific research pipeline combining Exa Search, Playwright, deep-research, text-humanization, and iterative Remi peer review."
---

# Deep Science Writer (End-to-End Pipeline)

This skill orchestrates a multi-stage pipeline for scientific research, combining neural search, browser automation, academic synthesis, and humanized writing. It merges the capabilities of Exa Search, Playwright, Google Science Skills, Deep Research, and Text Humanization into one cohesive workflow.

## 🎯 Trigger Conditions
- User asks to write a scientific article, literature review, or deep-dive research report.
- User requests comprehensive research using web searching and scraping (Exa + Playwright).
- The output requires rigorous academic citations (APA 7th) but a highly natural, human-like reading flow.

## 📋 Workflow Steps

### Phase 0: Asset Loading & Research Plan Discussion
1. Incorporate academic rigor from `nature-skills`, structured literature parsing from `academic-research-skills`, and cross-validation techniques from `superpowers`. Keep their principles active in context.
2. **Mandatory Pre-Flight Discussion:** Before launching any web searches or fetching any papers, formulate a preliminary research plan (proposed keywords, target databases, expected article structure, and goals).
3. Present this blueprint to the user to discuss the research direction.
   - Focus on delegating the heavy lifting (scraping, multi-page data extraction) to parallel subagents via `delegate_task` to protect the main context window.
4. **Halt & Wait:** You MUST wait for the user's "Explicit Approval" before proceeding to Phase 1.

### Phase 0.5: Subagent Dispatch (Mass Scale & Synthesis)
1. **Mandatory Delegation:** You must NOT execute Phase 1 and Phase 2 entirely in the main thread.
2. **Massive Parallel Sourcing:** You MUST spawn parallel subagents using `delegate_task` for literature discovery. **Each must retrieve and process over 700 papers:**
   - **Subagent A (Scopus Dedicated):** Exclusively use `scopus-mcp` (or terminal scripts with the API key) to retrieve 700+ high-impact papers from Elsevier Scopus. Subagent A MUST process these and output a dedicated "Scopus Synthesis Report" summarizing the trends and findings. In this report, Subagent A MUST explicitly cite at least 50 key papers from its 700+ pool.
   - **Subagent B (Google Science & Open Access):** Exclusively use `google-science-skills` APIs or Exa Search MCP to find 700+ complementary open-access papers. Subagent B MUST process these and output a dedicated "Open Science Synthesis Report". In this report, Subagent B MUST explicitly cite at least 50 key papers from its 700+ pool.
3. Spawn Subagent A and B concurrently with appropriate toolsets (`['web', 'terminal']`). Ensure their scripts handle API pagination, data chunking, and local file storage (e.g., saving metadata to CSV/JSON) to reach the 700+ paper threshold without exceeding memory limits.
4. **Subagent C (Master Synthesizer):** After A and B complete, you MUST spawn a third subagent, **Subagent C**. Pass both the Scopus and Open Science synthesis reports (which contain ~100 cited papers combined) to Subagent C. Its sole goal is to merge, critically analyze, and curate a final master synthesis that directly addresses the overarching research direction, explicitly selecting and citing exactly the top 50 best papers for the final manuscript.

### Phase 1: Neural & Academic Discovery (`exa-search` + `scopus-mcp` + `google-science-skills`)
1. **Journal Quality Filter**: ONLY include Q1 and Q2 papers. If a Q3 paper provides crucial evidence, you MUST explicitly mark it in the text/table with `[Q3]`. STRICTLY EXCLUDE any Q4 papers and ANY papers published by MDPI.
2. **Query Formulation**: Break down the user's topic into 3-5 distinct semantic search queries.
3. **Proactive Scopus API Search (High Priority)**: Actively deploy the `scopus-mcp` tools (`search_scopus` and `get_abstract_details`) to query the Elsevier Scopus database directly. This is the primary and most authoritative source. Bypass web UI scraping entirely by using these direct API tools.
4. **Neural Search**: Call the **Exa Search MCP** to supplement with contextually relevant articles, technical blogs, and open-access papers.
4. **Academic Databases**: Call relevant `google-science-skills` (e.g., PubMed, Semantic Scholar) to pull additional peer-reviewed metadata.
4. **Exhaustive Mapping (User Rule)**: Do NOT sample (e.g., just looking at 5 out of 20). Process the *exhaustive* set of relevant findings into a structured Markdown table: `| Title | Authors/Year | Key Finding | URL/DOI |`.

### Phase 2: Deep Extraction (`playwright-mcp` + `deep-research`)
1. **Dynamic Scraping**: For high-value sources that require JavaScript rendering, interaction, or are heavily dynamically loaded, use the **Playwright MCP** to navigate, wait for specific DOM selectors, and extract the full text.
2. **Synthesis**: Cross-reference extracted findings across multiple sources to validate claims and identify consensus vs. controversy. 

### Phase 3: Structural Drafting (`article-writing`)
1. Outline the article based on `article-writing` principles: strong hook, logical progression, evidence-backed claims, and clear logical headings.
2. Integrate data explicitly. Use block equations or Mermaid diagrams if explaining complex systems or workflows.
3. Format all inline citations and the final reference list strictly in **APA 7th** format. When generating via `python-docx`, programmatically implement APA hanging indents (`p.paragraph_format.first_line_indent = Inches(-0.5)` and `p.paragraph_format.left_indent = Inches(0.5)`) and ensure journal/book titles and volume numbers are properly italicized.

### Phase 4: Humanization & Polish (`text-humanizer`)
1. Review the generated draft and ruthlessly strip AI-isms, applying the strict **"No Fluff"** style profile.
2. **Banned AI Vocabulary**: "delve", "tapestry", "in conclusion", "crucial", "testament", "realm", "fosters", "underscores", "moreover".
3. **Style Adjustments**: 
   - Use varied sentence lengths (short, punchy sentences mixed with complex ones).
   - Prefer active voice over passive voice.
   - Remove introductory meta-commentary ("Here is the article...").
   - Ensure the prose flows like a subject-matter expert speaking directly to a peer.

### Phase 4.5: Anti-Hallucination & Evidence Verification
**Strict Requirement:** This phase MUST be completed before Remi (Phase 5) is allowed to review the manuscript.
1. **Extraction**: Scan the draft and extract every single in-text citation (e.g., Smith, 2024) and its corresponding Reference List entry.
2. **DOI/URL Liveness Test**: Use the `terminal` tool (via `curl -I`), Exa Search MCP, or a Python script (e.g., `requests.get` / `urllib`) to ping every DOI or URL in the reference list. For bulk or programmatic URL resolution when links are missing, execute `scripts/verify_urls.py` (uses `ddgs` and `requests`).
   - If a DOI/URL is dead (404) or fake: **Delete the citation and rewrite the affected claim**, or pause to find the correct, live DOI.
3. **Claim Grounding Check**: Cross-reference the specific claims made in the draft against the raw data/abstracts collected in Phases 1 & 2. 
   - If a claim overstates the actual findings (e.g., claiming "cures" when the abstract says "mitigates"), down-modulate the claim to match the evidence.
4. **Pass Condition**: Zero dead links, zero fake DOIs, and zero ungrounded claims. Only then proceed to Phase 5.

### Phase 5: Peer Review & Iteration (`remi`)
1. Load the `remi` skill (`skill_view(name='remi')`) to act as a strict Nature/Science-level peer reviewer.
2. Submit the Phase 4 draft to Remi for a rigorous evaluation against evidence backing, APA 7th formatting, logical flow, and academic tone.
3. **Iteration Loop**: Analyze Remi's critique. If there are any flaws, fluff, or stylistic complaints, apply the fixes and rewrite the draft.
4. Repeat the Remi review process until Remi approves the manuscript with zero critical concerns.

### Phase 6: Data Visualization & Final Document Generation (.docx)
1. **Statistical Plotting & Diagrams (Python)**: Use `matplotlib`/`seaborn` for data trends. For conceptual frameworks (like AHP or MCDA structures), generate Mermaid diagrams and convert them to PNGs using the `mermaid.ink` base64 API. *(Pitfall: Do not use kroki.io for complex Mermaid charts as it frequently returns 400 Bad Request; use mermaid.ink instead).* Save these images to a local `assets/` folder.
2. **Document Compilation (`python-docx`)**: You MUST NOT just output Markdown as the final product. Write a Python script using the `python-docx` library (`pip install python-docx` if necessary) to programmatically build the final Word document.
3. **Embed Assets**: Insert the generated Python plots/charts into the `.docx` file at the appropriate logical sections. Ensure formatting aligns with APA 7th standards (e.g., proper figure captions).
4. **Final Delivery**: Save the generated `.docx` file directly to the `D:\` drive (e.g., `D:\Research_Report.docx`). Deliver this absolute D:\ path to the user.

### Phase 7: Knowledge Base & NotebookLM Integration
1. **Obsidian Wiki Update**: Synthesize the core findings, literature insights, and strategic takeaways. Write or append this synthesis directly into the user's Obsidian Vault (`C:\Users\User\Documents\Obsidian Vault\Hermes\`) to maintain an ongoing, centralized knowledge base.
2. **NotebookLM Source Ingestion**: Utilize the `notebooklm` MCP tools to create a dedicated notebook for this research project. Upload all verified reference materials, full texts, or abstracts gathered during Phase 1 & 2 into NotebookLM as sources. This ensures the literature is permanently available for interactive querying, deep dives, and audio overview generation.

## 📚 Linked References
- `references/python-docx-manipulation.md`: Patterns for reading, creating, and safely removing XML paragraphs from `.docx` files.
- `references/academic-api-patterns.md`: Reliable curl and Python patterns for hitting Crossref and OpenAlex APIs, including critical URL-encoding fixes.
- `scripts/verify_urls.py`: Python script utilizing `ddgs` and `requests` to programmatically search and verify evidence URLs for Phase 4.5.

## ⚠️ Pitfalls & Strict Rules
- **No Hallucinated Citations:** Every claim MUST map to a real URL/DOI found during Phase 1/2.
- **Paywalled Literature (Elsevier/Scopus):** Standard APIs (Crossref/Exa) cannot fetch full text from closed databases. To bypass academic paywalls, spawn a `playwright` subagent to navigate to the article URL directly—if the host machine is on a university network, this automatically leverages IP-based access.
- **Action Over Planning:** Do not tell the user what you *will* do. Immediately start executing Exa Search and Playwright tool calls.
- **Table First:** Always build and present the literature/evidence table *before* writing the final prose.
