# Deep Research Agent — 最終安全與程式碼審查報告

**審查日期：** 2026-06-10
**審查範圍：** 完整程式碼庫（README.md、skills/deep-science-writer/、skills/remi/）
**審查方式：** 平行執行 Security Auditor 與 Code Reviewer 兩個 Subagent，人工交叉驗證

---

## 總覽

| 維度 | 發現數 | 審查者 |
|------|--------|--------|
| 🔒 安全漏洞 | 3 High / 3 Medium / 2 Low / 2 Info | Security Auditor |
| 🔍 程式碼品質 | 5 Critical / 7 Important / 8 Suggestion | Code Reviewer |
| **合計（去重）** | **8 Critical+High / 8 Medium+Important / 9 Low+Suggestion** | 兩者合併 |

---

## 合併發現矩陣

### 🔴 必須立即修復（Critical / High）

| ID | 問題 | 檔案 | 類型 | 來源 |
|----|------|------|------|------|
| **F1** | **SSL 憑證驗證被完全禁用** — `ctx.check_hostname = False` + `ctx.verify_mode = ssl.CERT_NONE`，所有對 OpenAlex 的 HTTPS 請求暴露於 MITM 攻擊 | `references/academic-api-patterns.md:17-19` | 🔒🔍 Critical/High | 兩者共識 |
| **F2** | **命令注入風險** — `curl -I` 建議將未經消毒的 DOI/URL 直接傳入 shell，惡意字串（`;`、`` ` ``、`$()`）可造成任意命令執行 | `SKILL.md` Phase 4.5 | 🔒 High | Security |
| **F3** | **動態 runtime pip install 無完整性檢查** — `except ImportError: subprocess.check_call(["pip", "install", ...])` 無版本 pin、無 hash 驗證、無 scope 限制，供應鏈攻擊可直接 RCE | `references/python-docx-manipulation.md:7-15` | 🔒 High | Security |
| **F4** | **`except: pass` 吞掉所有例外** — `verify_urls.py` 的反幻覺驗證在失敗時無聲返回空結果，整個保證形同虛設 | `scripts/verify_urls.py:25-28` | 🔍 Critical | Code Review |
| **F5** | **硬編碼使用者名稱 `User`** — Obsidian 路徑 `C:\Users\User\...` 在所有非 `User` 帳號的機器上都會失敗且不報錯 | `SKILL.md` Phase 7 | 🔍 Critical | Code Review |
| **F6** | **硬編碼 `D:\` 無備援路徑** — 單分割區機器直接 crash，輸出遺失 | `SKILL.md` Phase 6 | 🔍 Critical | Code Review |
| **F7** | **無限制 Remi 審查迴圈** — 「持續到無 Critical 問題」沒有 max iterations，可能無限循環耗盡 API 配額 | `SKILL.md` Phase 5 | 🔍 Critical | Code Review |
| **F8** | **未驗證的使用者查詢傳遞給 subagent** — 惡意研究主題可注入指令、或 prompt injection 影響子代理行為，且 subagent 有 terminal 權限 | `SKILL.md` Phase 0.5 | 🔒 Medium | Security |

### 🟠 應於本開發週期修復（Medium / Important）

| ID | 問題 | 檔案 | 類型 | 來源 |
|----|------|------|------|------|
| **F9** | 403 狀態碼誤標為 `'Verified Alive'` — 字串比對脆弱 | `scripts/verify_urls.py:31` | 🔍 Important | Code Review |
| **F10** | python-docx 遍歷時原地刪除 element（in-place modification） | `references/python-docx-manipulation.md:38-40` | 🔍 Important | Code Review |
| **F11** | `sys.exit(1)` 粗暴終止程序 — 單一圖表失敗就整條 pipeline 掛掉 | `scripts/mermaid_to_png.py:24` | 🔍 Important | Code Review |
| **F12** | `ddgs` vs `duckduckgo_search` 套件混淆 — 用的是非官方 wrapper | `scripts/verify_urls.py:6` | 🔍 Important | Code Review |
| **F13** | 700+ 論文檢索無分頁/限速範例碼 — API 很容易 timeout | `SKILL.md` Phase 0.5 | 🔍 Important | Code Review |
| **F14** | 零測試基礎建設 — 無法驗證回歸、反幻覺保證無法程式化驗證 | 全 repo | 🔍 Important | Code Review |
| **F15** | Subagent 失敗時無容錯機制 — 無 circuit-breaker / partial-failure path | `SKILL.md` Phase 0.5 | 🔍 Important | Code Review |
| **F16** | 研究查詢洩漏至第三方搜尋引擎 — DuckDuckGo 會收到敏感論文資訊 | `scripts/verify_urls.py:10-22` | 🔒 Medium | Security |
| **F17** | 無路徑穿越保護 — 所有檔案寫入操作無基底目錄 allowlist | `SKILL.md` Phase 6, 7 | 🔒 Medium | Security |

### 🟢 建議改善（Suggestion / Low / Info）

| ID | 問題 | 原始評級 | 來源 |
|----|------|----------|------|
| S1 | Requirements 無版本鎖定 | Suggestion | Code Review |
| S2 | Mermaid theme 硬編碼為 default | Suggestion | Code Review |
| S3 | verify_urls timeout 5s 太短無法配置 | Suggestion | Code Review |
| S4 | 宣稱 MIT License 但無 LICENSE 檔案 | Suggestion | Code Review |
| S5 | Remi skill 編號跳號（缺 9、8 重複） | Suggestion | Code Review |
| S6 |「Action Over Planning」與 Phase 0 強制 halt 矛盾 | Suggestion | Code Review |
| S7 | 無 `.gitignore`，產出檔案可能被 commit | Suggestion | Code Review |
| S8 | 禁用 AI 詞彙列表應為機器可讀格式 | Suggestion | Code Review |
| S9 | README 暴露本機檔案系統路徑 | Low | Security |
| S10 | 鼓勵透過大學網路繞過付費牆 | Low | Security |
| I1 | Scopus API Key 未寫在程式碼中（良好做法） | Info 👍 | Security |
| I2 | `ddgs` 未鎖版本 | Info | Security |

---

## 風險關聯圖

```
F1 (SSL 關閉) ───→ 攻擊者可注入假論文資料
                       │
                       ▼
F2 (curl 注入) ──→ 惡意 DOI 觸發命令執行
                       │
                       ▼
F7 (無窮迴圈) ───→ 成本失控，資源耗盡
                       │
                       ▼
F4 (pass 吞錯) ──→ 反幻覺保證變笑話
                       │
                       ▼
F8 (未驗證輸入) ─→ Subagent prompt injection
                       │
                       ▼
F3 (pip 動態安裝) ──→ 供應鏈 RCE
```

**最嚴重的攻擊鏈：** F1 → 注入虛假論文 → F2 → 透過 `curl` 執行任意命令 → 完整主機淪陷。這條鏈只需要攻擊者與 victim 在同一網路即可觸發。

---

## 正面觀察

- ✅ API Key 僅以環境變數形式存在，無硬編碼
- ✅ `verify_urls.py` 使用 `requests.get()`（安全）而非 `curl`（腳本本身正確）
- ✅ `mermaid_to_png.py` 使用 base64+JSON 避免字串插值風險
- ✅ Remi skill 有明確的「禁止幻覺引用」規則
- ✅ Git remote 使用 HTTPS 無內嵌憑證
- ✅ 7-phase 架構設計清晰，雙源檢索理念紮實
- ✅ Pitfalls 章節展現真正的實戰經驗

---

*本報告由 Security Auditor + Code Reviewer 平行產出，經人工交叉驗證。*
