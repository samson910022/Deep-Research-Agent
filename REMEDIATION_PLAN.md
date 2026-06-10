# 🔧 Deep Research Agent — 修復計畫

**目標：** 將本專案從「REQUEST CHANGES」提升至可安全部署的狀態
**優先級分級：** P0 (立即) → P1 (本 sprint) → P2 (下個 sprint) → P3 (後續)

---

## Phase 1 — 立即修復（P0：上線前必須完成）

### P0-1 🔒 恢復 SSL 憑證驗證
**檔案：** `skills/deep-science-writer/references/academic-api-patterns.md`
**對應發現：** F1
**Action：**
```python
# 移除這兩行
# ctx.check_hostname = False
# ctx.verify_mode = ssl.CERT_NONE

# 保留預設 SSL context，即可正常驗證 OpenAlex 的商用憑證
ctx = ssl.create_default_context()
```
**驗證方式：** 執行 `python3 -c "import ssl; ctx=ssl.create_default_context(); print('SSL OK')"`

---

### P0-2 🚫 移除 `curl -I` 命令注入風險
**檔案：** `skills/deep-science-writer/SKILL.md` Phase 4.5
**對應發現：** F2
**Action：**
- 將 Phase 4.5 的 `curl -I` 建議改為僅限 Python `requests.get()` 的方式
- 加入 URL 驗證規則：DOI 必須符合 `https://doi.org/10.\d{4,}/[\w.\-/:]+` 格式
- 明確寫入：**「Only use `requests.get(url, timeout=5)` — never `curl` with unsanitized input」**

---

### P0-3 🔧 修復 `except: pass` 吞錯
**檔案：** `skills/deep-science-writer/scripts/verify_urls.py`
**對應發現：** F4
**Action：**
```python
except Exception as e:
    print(f"[WARN] verify_urls: query '{q}' failed: {e}", file=sys.stderr)
    continue  # 或 re-raise，視 context 決定
```

---

### P0-4 📁 硬編碼路徑改為環境變數 + 備援
**檔案：** `skills/deep-science-writer/SKILL.md` Phase 6 & Phase 7
**對應發現：** F5, F6
**Action：**
- Obsidian 路徑：`%OBSIDIAN_VAULT_PATH%\Hermes\`（預設 `C:\Users\%USERNAME%\Documents\Obsidian Vault\Hermes\`）
- 輸出 Docs：`%OUTPUT_DIR%\Research_Report.docx`（備援順序 `D:\` → `Documents\` → 環境變數）
- 在 SKILL.md frontmatter 加入可配置變數區塊，明確要求使用者修改

---

### P0-5 🔄 Remi 審查加入上限
**檔案：** `skills/deep-science-writer/SKILL.md` Phase 5
**對應發現：** F7
**Action：**
```
### Phase 5: Peer Review & Iteration
...
4. **Maximum 3 review rounds.** If Remi still has concerns after round 3,
   document each unresolved concern as a "Limitations" subsection and proceed to Phase 6.
```

---

## Phase 2 — 本開發週期（P1）

### P1-1 📦 鎖定依賴版本、移除動態 pip install
**檔案：** `skills/deep-science-writer/references/python-docx-manipulation.md`
**對應發現：** F3
**Action：**
- 新增 `requirements.txt` 鎖定所有版本
- 將參考文件中的動態安裝範例改為啟動時檢查
```python
import importlib.metadata
required = {"python-docx": "1.1.2", "PyMuPDF": "1.24.0", "requests": "2.32.0"}
for pkg, ver in required.items():
    assert importlib.metadata.version(pkg) == ver, f"{pkg}=={ver} required"
```

### P1-2 🛡️ 輸入驗證閘道
**檔案：** `skills/deep-science-writer/SKILL.md` Phase 0
**對應發現：** F8
**Action：**
- Phase 0 加入研究查詢的消毒步驟：移除 `;`、`|`、`$()`、`` ` ``、`\` 等 shell metacharacter
- 限制 Subagent 工具權限：不需要 terminal 的 subagent 就不給 terminal

### P1-3 🧪 建立測試基礎建設
**對應發現：** F14
**Action：**
- `tests/` 目錄
- `test_verify_urls.py`：mock DDGS + requests.get，測試 alive/403/failed 狀態機
- `test_mermaid_to_png.py`：mock urllib.request，測試 base64 編碼邏輯
- `test_docx_manipulation.py`：測試 element 移除不 corrupt XML tree

### P1-4 🧭 分頁範例碼
**檔案：** `skills/deep-science-writer/SKILL.md` Phase 0.5、`references/academic-api-patterns.md`
**對應發現：** F13
**Action：**
- 在 `academic-api-patterns.md` 新增 pagination template
- 含 rate-limit backoff（`time.sleep(1)`）與 max_pages guard

### P1-5 🗺️ 路徑允許清單
**檔案：** `scripts/mermaid_to_png.py` + SKILL.md Phase 6/7
**對應發現：** F17
**Action：**
```python
SAFE_BASES = ["D:\\", os.path.expanduser("~/Documents/Obsidian Vault/Hermes/")]
def safe_path(dest):
    abs_dest = os.path.abspath(dest)
    return any(abs_dest.startswith(os.path.abspath(base)) for base in SAFE_BASES)
```
拒絕含 `..`、`~`、`%` 的路徑。

---

## Phase 3 — 下個開發週期（P2）

### P2-1 🔄 改用 `duckduckgo_search` 官方套件
**對應發現：** F12
**Action：**
- `pip install duckduckgo_search` 取代 `ddgs`
- 更新 `verify_urls.py` import 與 README 安裝說明

### P2-2 ⏱️ 403 狀態碼明確化
**對應發現：** F9
**Action：**
- `verify_urls.py` 改用整數 status code 判斷（非字串）
- 403 獨立標示為 `exists_restricted`

### P2-3 🧹 原地修改文件修復
**對應發現：** F10
**Action：**
```python
to_remove = [p._element for p in doc.paragraphs[start_idx:]]
parent = to_remove[0].getparent()
for elem in to_remove:
    parent.remove(elem)
```

### P2-4 🚦 `sys.exit(1)` 改為自訂例外
**對應發現：** F11
**Action：**
```python
class MermaidGenerationError(Exception): pass
# 取代 sys.exit(1)
raise MermaidGenerationError(...)
```

### P2-5 🤝 Subagent Partial Failure Recovery
**對應發現：** F15
**Action：**
- SKILL.md Phase 0.5 加入容錯段落
- Subagent A 失敗 → B 擴充至 1000+ papers
- 兩者皆失敗 → abort + user notification

### P2-6 🔒 DuckDuckGo 改為 DOI.org/Crossref 直接驗證
**對應發現：** F16
**Action：**
- 在 `verify_urls.py` 加入 `verify_doi(doi)` 使用 Crossref API
- 只在 DOI 無法直接解析時才 fallback 到 DuckDuckGo

---

## Phase 4 — 持續改善（P3）

| # | 項目 | 估計工時 | 備註 |
|---|------|---------|------|
| P3-1 | 新增 `requirements.txt` 鎖版本 | 15 min | |
| P3-2 | 新增 `.gitignore` | 5 min | |
| P3-3 | 新增 LICENSE 檔案（MIT） | 5 min | |
| P3-4 | Mermaid theme 可配置 | 30 min | |
| P3-5 | verify_urls timeout 設為可配置參數 | 15 min | |
| P3-6 | Remi skill 編號修正 | 5 min | |
| P3-7 | 矛盾指令修正（Action Over Planning vs Phase 0） | 10 min | |
| P3-8 | 禁用 AI 詞彙清單改為 YAML/machine-readable | 20 min | |
| P3-9 | README 路徑改為 `<placeholder>` 格式 | 10 min | |
| P3-10 | Paywalled access 文字修正 | 5 min | |

---

## 修復時程估計

| Phase | 項目數 | 預估總工時 | 優先度 |
|-------|--------|-----------|--------|
| P0 🔴 | 5 | 2–3 小時 | **上線前必須** |
| P1 🟠 | 5 | 4–6 小時 | **本 sprint** |
| P2 🟡 | 6 | 3–4 小時 | **下個 sprint** |
| P3 🟢 | 10 | 1.5 小時 | **持續改善** |
| **Total** | **26** | **10–14 小時** | |

---

## 快速修復指令（若要以 patch 形式自動套用）

```bash
# 目錄結構
cd ~/projects/Deep-Research-Agent

# 1. 修復 ssl.py 移除 ssl 繞過
# 2. 修復 verify_urls.py 加上錯誤輸出
# 3. 更新 SKILL.md Phase 4.5 移除 curl 建議
# 4. 更新 SKILL.md Phase 5 加入 max 3 rounds
# 5. 更新 SKILL.md Phase 6/7 路徑改為可配置變數
# 6. 新增 requirements.txt
# 7. 新增 .gitignore
# 8. 新增 LICENSE (MIT)
```

---

*修復計畫基於 Security Audit + Code Review 報告，優先級依風險等級與實作複雜度排列。*
