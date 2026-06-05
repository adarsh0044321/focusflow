# FocusFlow v1.1.0 — Universal API Support & Stealth History HUD

This release focuses on adding compatibility for third-party LLM providers, implementing a visual study history dashboard, and making the OCR capture and keyword retrieval pipelines more resilient.

## 🚀 Key Features & Enhancements

### 🧠 1. Universal API Support (Ollama, DeepSeek, Groq, OpenRouter)
* **Custom API Base URL & Models**: Route queries to any OpenAI-compliant backend by specifying a custom API Base URL and custom model string under **Settings -> Online Settings** (e.g. `http://localhost:11434/v1` for local Ollama, `https://api.deepseek.com` for DeepSeek).
* **Dropdown Overrides**: Overrides default OpenAI dropdown choices when a custom model name is entered.

### 📜 2. Draggable History HUD Panel
* **Solves Dashboard**: Access your last 100 solves via the new **History** tab. View metadata, cleaned OCR texts, and formatted answers with green highlight tags.
* **Auxiliary Screenshot Viewer**: Opens saved screenshots in a popup window protected by the display affinity guard (invisible to screen share/captures).
* **Solves Restoration**: Restore any past solve directly back into the main HUD panels.

### 👁️ 3. Math & Programming Code Preservation
* Lowered OCR noise threshold to `30%` and whitelisted math/coding operators (`+-*/=<>()[]{}^_\|,.?!&|:;`) to preserve complex mathematical formulas and matrix declarations.

### 🧠 4. Optimized Keyword Search (Stemming & Stop-Words)
* Ignores common English particles (stop words) and uses whole-word set intersection with a stemming fallback for keywords >= 4 characters, preventing false substring matches.

### ⚙️ 5. Subprocess & Daemon Resilience
* **Orphaned Process Reuse**: FocusFlow checks the health of `llama-server.exe` on startup. If a healthy local server is already running on the port, it attaches to it rather than crashing.
* **Non-Windows Silence**: Win32 display affinity thread is skipped on non-Windows platforms.
