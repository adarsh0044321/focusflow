# FocusFlow v1.4.0 — Proctoring Exit Modal, Dynamic Coding App, Inline PDF & GGUF Model Selector

This release resolves critical bugs in FocusFlow's proctoring exit sequence, adds inline PDF viewing within WebView2, whitelists custom coding applications dynamically in Moderate Mode, and introduces native file selection for custom GGUF models.

## 🚀 Key Features & Enhancements

### 🚪 1. Smart Proctoring Early-Exit Modal
* **Confirmation Dialog**: Replaced simple alert prompts with a full React confirmation modal that freezes the focus timer.
* **Exit Status Routing**: Prompts users to log their exit status as "Goal Completed Successfully" (regular completion), "Partially Completed" (partial credit), or "Aborted/Abrupt Exit" (score penalty applied).
* **Distinct Feedback**: Displays dynamic green, amber, or red toasts depending on the selected exit reason.

### 💻 2. Dynamic Coding App Whitelisting
* **Moderate Mode Subject Selector**: In Moderate Mode, when the chosen subject is "Computer Science", users can select/whitelist their custom coding application (e.g. VS Code, PyCharm, IDLE).
* **Dynamic Whitelist Injection**: Dynamically whitelists the selected coding executable, preventing the proctoring engine from closing it on launch.

### 📄 3. Inline PDF View Integration
* **Dynamic MIME Association**: Registers the `application/pdf` MIME type directly inside the Python local HTTP server. This forces WebView2 to render study files inline in the HUD viewport rather than downloading them externally or triggering Chrome browser launches.

### 🧠 4. Native GGUF Model Selection & Guidelines
* **Native File Dialog**: Spawns a topmost Windows Open File browser to select custom `.gguf` files saved anywhere on the machine, writing the absolute path directly to settings.
* **Model Portability**: Resolved relative path bugs so that moving the application directory (`dist/`) does not break offline LLM initialization.
* **RAM & Specs Documentation**: Integrated Hugging Face download links and RAM specifications (e.g., Phi-3 Mini for 8GB+ RAM, Qwen-2.5 1.5B for 4GB-6GB RAM, Llama-3 8B for 16GB+ RAM) directly in Settings and the README.

---

# FocusFlow v1.3.0 — Unified AI Engine & Strict Lazy LLM Controller

This release consolidates FocusFlow modes into a single unified application entry and provides optimized lazy lifecycle resource control for the offline LLM model.

## 🚀 Key Features & Enhancements

### ⚙️ 1. Unified Engine Selection
* **UI Controls**: Exposes a unified `"AI MODEL ENGINE"` dropdown in settings allowing users to choose from Online (`gpt-4o`, `gpt-4o-mini`), Offline (`Phi-3 GGUF`), and Combined (Auto Hybrid) solve profiles.
* **Auto-Fallback Routing**: Resolves the selected profile dynamically. In combined mode, queries the local offline LLM first, falling back to online APIs if the server is still loading or configured keys are available.

### 🧠 2. Strict Lazy LLM Resource Controller
* **Tab Visibility Detection**: Starts the offline LLM backend (`llama-server.exe`) dynamically only when the Study AI Doubts Solver panel/tab is actively visible/focused on the screen.
* **Real-time Config Swaps**: Swapping model engine configs while the AI panel is active starts or terminates the local server immediately.
* **Hard Memory Reclamation**: Triggers native `taskkill` on server stop. When the AI solver is minimized, closed, or the application itself is exited, any background `llama-server.exe` process is terminated immediately to free up 2.4GB of system RAM.

### 📦 3. Consolidated Entry Point & Package Specification
* **Single Specification**: Merged separate packaging specs into a single unified `FocusFlow.spec`.
* **Legacy Wrappers Removed**: Deleted redundant spec manifests and launcher scripts (`main_online.py`, `main_offline.py`), wrapping all bootstrap controls inside `main.py`.

---

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
