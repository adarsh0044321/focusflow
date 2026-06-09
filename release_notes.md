# FocusFlow v1.2.0 — Triple Mode Partitioning (Online, Offline, Combined)

This release partitions FocusFlow into three distinct run configurations, allowing complete isolation of execution profiles, custom adaptive layouts, and dedicated packaging.

## 🚀 Key Features & Enhancements

### ⚙️ 1. Engine Isolation (Online / Offline / Combined)
* **Bootstrap Launchers**: Three dedicated launch points: `main_online.py` (locks application to Online-only solving), `main_offline.py` (locks application to local Offline-only solving), and `main.py` (Combined/Hybrid solving with user-toggle controls).
* **Bypassed Lifecycles**: Booting Online-only completely bypasses `llama-server.exe` background startup and polling. Booting Offline-only skips all OpenAI API network checks and rotations.

### 🎨 2. Adaptive Settings UI
* **Dynamic Tab Hiding**: Hides irrelevant setting frames (e.g. online API fields in Offline mode, and GGUF parameters in Online mode) to keep configuration clean.
* **Auto-Scaling Geometry**: The settings dialog automatically adjusts its window height depending on the active launcher (`500x460` for Online, `500x400` for Offline, and `500x640` for Combined).
* **Config Safety**: Settings updates only apply changes relevant to the active run profile, preventing config overrides.

### 📦 3. Dedicated Build Targets
* **Spec Targets**: Setup PyInstaller specification profiles (`FocusFlow-Online.spec`, `FocusFlow-Offline.spec`, and `FocusFlow-Combined.spec`) to easily compile isolated binaries.

---

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
