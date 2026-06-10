# Deep Research Agent

**Deep Science Writer** is an industrial-grade, end-to-end scientific research pipeline and AI agent skill. Designed for the Hermes/ECC framework, it completely automates the literature review process: from massive-scale dual-source database querying (700+ papers) down to anti-hallucination verification, Nature/Science-level peer review, `.docx` compilation, and Obsidian/NotebookLM knowledge base ingestion.

## 🌟 Key Features

* **Massive Parallel Dual-Sourcing (1,400+ Papers):** Uses a Subagent architecture to concurrently scrape Elsevier Scopus (Subagent A) and Open Science databases like OpenAlex/Crossref (Subagent B).
* **Funnel Synthesis:** Distills 1,400+ papers down to the top 50 most relevant, high-quality citations using a Master Synthesizer (Subagent C).
* **Strict Quality Control:** Explicitly targets Q1-Q2 journals. Marks Q3 when strictly necessary. **Bans all Q4 and MDPI publications.**
* **Zero-Hallucination Guarantee (Phase 4.5):** Automatically runs live HTTP `requests` tests against every generated DOI to ensure 100% validity. Cross-references generated claims against raw abstracts to prevent AI overstatement.
* **Automated Peer Review:** Integrates the `remi` peer-review skill *(named in tribute to my academic advisor, Remi Chauvy)* to aggressively strip "AI fluff" (e.g., "delve", "tapestry") and enforce rigorous academic tone.
* **Hands-Free Output:** Programmatically builds a fully formatted Microsoft Word document (`.docx`) with APA 7th hanging indents and auto-generated data visualizations.
* **Knowledge Management Loop:** Automatically saves research summaries to your local **Obsidian Vault** and uploads reference materials to **Google NotebookLM** for future interactive queries.

---

## 📋 Prerequisites

To run this skill successfully, your host environment must be configured with the following dependencies and Model Context Protocol (MCP) servers:

### 1. System Requirements
* **Hermes Agent** (or a compatible ECC/Claude Code runner).
* **Node.js** (v18+ recommended) and `npx` for running MCP servers.
* **Python 3.10+** (in your system PATH or agent's virtual environment).

### 2. Python Dependencies
The agent relies on Python to generate documents and verify links.
```bash
pip install python-docx PyMuPDF requests matplotlib seaborn pandas
```

### 3. Required MCP Servers
Add these to your `config.yaml` or `claude_desktop_config.json`:

* **Scopus MCP (`scopus-mcp`)**
  * Required for Subagent A's premium literature retrieval.
  * **API Key:** Requires a free Elsevier Scopus API Key (`SCOPUS_API_KEY`). Apply at the [Elsevier Developer Portal](https://dev.elsevier.com/).
* **NotebookLM MCP (`notebooklm-mcp-server`)**
  * Required for Phase 7 knowledge ingestion.
  * **Auth:** Must run `npx notebooklm-mcp-server auth` once in your terminal to authenticate your Google Account locally.
* **Exa Search MCP** (Highly Recommended)
  * Used for neural search fallback and broad open-access discovery.
* **GitHub MCP & Playwright MCP** (Optional but recommended for broader functionality).

### 4. Local Environment
* **Obsidian:** The skill looks for `%OBSIDIAN_VAULT_PATH%\Hermes\` (fallback: `%USERPROFILE%\Documents\Obsidian Vault\Hermes\`). Update `SKILL.md` Phase 7 or set the environment variable if your vault is located elsewhere.
* **Output Drive:** The skill saves the final `.docx` to `%OUTPUT_DIR%\Research_Report.docx` (fallback order: `D:\` → `%USERPROFILE%\Documents\`). Set the `%OUTPUT_DIR%` environment variable or adjust `SKILL.md` Phase 6 to match your system.

---

## 🚀 Installation

Clone this repository into your agent's skills directory:

```bash
cd <AGENT_SKILLS_DIR>
git clone https://github.com/YOUR_USERNAME/deep-research-agent.git
```
*(Replace `<AGENT_SKILLS_DIR>` with your agent's skills path, e.g., `~/.hermes/skills/` or `.agents/skills/` for the ECC framework).*

---

## 🧠 The 7-Phase Architecture

1. **Phase 0 & 0.5 (Plan & Dispatch):** The agent formulates a search plan and halts for your explicit approval. Once approved, it spawns parallel subagents to fetch 700+ papers each from Scopus and OpenAlex.
2. **Phase 1 (Discovery):** Enforces journal quality limits (Q1-Q2 only, bans MDPI).
3. **Phase 2 (Deep Extraction):** Consolidates metadata, abstracts, and key findings.
4. **Phase 3 (Structural Drafting):** Outlines the article with evidence-backed claims and APA 7th citations.
5. **Phase 4 & 4.5 (Anti-Hallucination):** Strips AI vocabulary. Pings all DOIs to ensure they resolve (404 = citation deleted).
6. **Phase 5 (Remi Review):** An internal peer-review loop that critiques and rewrites the draft until academic standards are met. *(Named in tribute to my academic advisor, Remi Chauvy).* 
7. **Phase 6 (Compilation):** Python scripts draw Mermaid/Matplotlib charts and compile the final `.docx`.
8. **Phase 7 (Knowledge Graph):** Updates Obsidian and pushes papers to NotebookLM.

---

## 💻 Usage Example

Simply trigger the agent with a research prompt:

> *"Please use the deep-science-writer skill to research the sociological and psychological acceptance of sustainability policies, segmented by age (public) and firm size (SMEs vs Large Enterprises)."*

The agent will take over, present a blueprint, ask for your approval, and then execute the entire pipeline autonomously.

---
**License:** MIT
