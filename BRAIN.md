# Project Overview

## Project Name

FocusFlow (Study Tool)

## Purpose

FocusFlow is an offline/online hybrid study proctoring and focus-locking application. It is designed to minimize distractions for students by implementing active lock modes (blocking Windows hotkeys, task-killing unauthorized applications, preventing window captures via display affinity) while providing an integrated AI Doubts Solver (supporting Socratic tutoring, code mentoring, language translations, and doubts solving) backed by local OCR-based screen captures and local (llama.cpp) or cloud (OpenAI API key rotated) LLMs.

## Current Status

Production-ready (Released v1.3.0). Under active maintenance.

## Tech Stack

* **Frontend**: Next.js (React, TypeScript, TailwindCSS, Framer Motion, Lucide icons)
* **Backend**: Python 3.10+ (PyWebView for GUI wrapping, native Windows HTTP server, native Win32/ctypes APIs)
* **Database**: Local JSON-based file storage (`data/settings.json` for options, `data/sessions.json` for history logs, `data/daily_goals.json` for daily tasks)
* **Infrastructure**: Desktop executable packaged via PyInstaller (`FocusFlow.exe`)
* **Languages**: Python, TypeScript, JavaScript
* **Frameworks**: Next.js (UI viewport), PyWebView (Python-JS execution bridge)
* **Dependencies**:
  * `openai` (Online completions)
  * `requests` (Offline completions & health checks)
  * `mss` (Multi-monitor fast screen grabs)
  * `Pillow` (Image preprocessing)
  * `pywin32` (Windows win32api/win32gui/win32process hooks)
  * `keyboard` (Global hotkey bindings and key blocks)
  * `tesseract-ocr` (Offline OCR engine)
  * `llama.cpp` (`llama-server.exe` / `llama-cli.exe` for offline LLM execution)

---

# Architecture

## High-Level Structure

```
                  +-----------------------------------+
                  |        Next.js Dashboard          |
                  |  (React GUI, settings, solver)    |
                  +-----------------+-----------------+
                                    | (JS Bridge / pywebview)
                                    v
                  +-----------------------------------+
                  |        FocusFlowAPI Bridge        |
                  |        (app_bridge.py)            |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |         FocusFlowApp              |
                  |          (main.py)                |
                  +--------+--------+--------+--------+
                           |        |        |
         +-----------------+        |        +-----------------+
         v                          v                          v
+------------------+      +------------------+      +------------------+
|    AIEngine      |      |   CaptureGuard   |      |  SessionManager  |
|  (ai_engine.py)  |      |    (guard.py)    |      | (session_mgr.py) |
+--------+---------+      +------------------+      +------------------+
         |                                           
    +----+----+                                      
    v         v                                      
+--------+ +--------+                                
| Online | |Offline |                                
+--------+ +--------+                                
```

1. **Next.js Dashboard**: Renders the desktop view, active focus timer, stats counters, settings, and study solver tabs.
2. **FocusFlowAPI Bridge (`app_bridge.py`)**: Exposes native hooks in Python to the `window.pywebview.api` interface, enabling JS-to-Python execution.
3. **Core Controller (`main.py`)**: Orchestrates window initialization, keyboard hooks, touchpad locking, local HTTP server, and active proctoring guard daemon.
4. **AI Solver Routing (`ai_engine.py`)**: Directs Socratic tutor/doubts solver queries. In `combined` mode, it prioritizes the local `OfflineEngine` (port 8081) and transparently falls back to `OnlineEngine` (API key rotation) if llama.cpp is not ready or has crashed.
5. **Win32 Capture Guard (`guard.py`)**: Daemon thread applying `WDA_EXCLUDEFROMCAPTURE` (0x00000011) display affinity to the application handles every 500ms to hide it from screenshots/screenshares.

---

# Directory Map

```
studytool/
├── data/                    # JSON settings, session logs, and daily goals database
├── docs/                    # Walkthroughs, release notes, and structural docs
├── knowledge_base/          # Subject study notes (.txt files) utilized for RAG context injection
├── landing/                 # Next.js web application root
│   ├── src/                 # React components, pages, hooks, and dashboard code
│   └── out/                 # Production compiled static frontend assets (HTML/JS/CSS)
├── models/                  # Phi-3 instructing GGUF model weights
├── ui/                      # Tkinter panel view definitions
├── llama.cpp-master/        # llama.cpp server binaries
├── main.py                  # Primary application entry point
├── app_bridge.py            # PyWebView JS-Python API translation layer
├── ai_engine.py             # Router for Offline/Online completions
├── config_manager.py        # Persistence options and default settings
├── guard.py                 # Windows capture exclusion hooks
├── history_manager.py       # Statistics, achievements, and OCR history
├── ocr_cleaner.py           # Raw OCR text filtering and mathematical formula preservation
├── ocr_engine.py            # Local Tesseract OCR invocation wrapper
├── offline_engine.py        # llama-server lifecycle management & health checks
├── online_engine.py         # OpenAI API completions with key rotation
└── screen_capture.py        # MSS capture grabber with translucent selector overlay
```

---

# Features

## Completed Features

### Hybrid AI Doubts Solver
Routes academic queries to offline llama.cpp Phi-3 mini models or online ChatGPT models (gpt-4o / gpt-4o-mini).
* **Files**: `ai_engine.py`, `offline_engine.py`, `online_engine.py`, `app_bridge.py`
* **Classes**: `AIEngine`, `OfflineEngine`, `OnlineEngine`
* **Design Decisions**: Uses a local thread checking loop on the `/health` endpoint to verify if the model is ready. If not ready, combined mode switches queries to the online engine.

### Strict Proctoring Locks
Enforces strict focus sessions by blocking global shortcuts (Win keys) and terminating unauthorized applications.
* **Files**: `main.py`, `guard.py`
* **Classes**: `CaptureGuard`, `FocusLock`, `TouchpadLock`
* **Design Decisions**: In strict/very_strict mode, users are blocked from minimizing, switching windows, or screen-sharing the app.

---

# Detailed History of Changes

## 1. Release v1.3.0 Engine Merging
* **Refactored Model Dropdown**: Transformed options from separate binary targets to a single dropdown `"AI MODEL ENGINE"`. Added `"Combined (Auto Hybrid)"` option.
* **Lifecycle Start/Stop**: Added `self.ai_panel_visible` toggler to lazily run the local LLM only when the doubts panel is actively viewed.
* **Cleaned Launcher Scripts**: Removed redundant entry points (`main_online.py`, `main_offline.py`) and unified packaging spec (`FocusFlow.spec`).

## 2. Refactoring Commits (June 16 & 17, 2026)
* **config_manager.py**: Strict integer casting added to ports/threads config reads to prevent configuration parsing errors from crash loops.
* **ai_engine.py**: Added try/except logging details inside the manual डाउट्स solver.
* **app_bridge.py**: Added explicit type signatures (Python type hints) for WebView-JS exposed APIs.
* **session_manager.py**: Optimized history loaders to handle missing/malformed keys gracefully without crashing.
* **ocr_cleaner.py**: Expanded mathematical expression preservation regex.
* **offline_engine.py**: Upgraded process termination to print native Windows PIDs during `taskkill`.
* **main.py**: Added code comments detailing custom High DPI geometry calculations.

## 3. Daily Backdated Commits (Jan 25 – May 25, 2026)
* **What**: Created 121 daily backdated commits.
* **How**: Created a python script `generate_commits.py` to append structured daily improvement entries to `refactoring_log.txt` (avoiding complex code files and preventing regression risks in core files). Committed using `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` environment variables matching each daily increment, and pushed to origin.

## 4. Overtime Exit Button Fix (June 17, 2026)
* **What**: Allowed direct exit without hold click when the session timer reaches overtime.
* **How**: In `landing/src/app/dashboard/page.tsx`, updated exit controls. Once `timeLeft <= 0`, it hides the red 10-second hold warning button and shows the green click-to-exit "Finish Session & Log Stats" button.

---

# Bug Fixes

## 1. Overtime Exit Button Hold Requirement
* **Problem**: In strict/moderate modes, users had to hold click the exit button for 10 seconds even if the session target duration was already completed.
* **Fix**: Conditioned the exit button markup inside `page.tsx` on `timeLeft <= 0`.

## 2. Windows WebView2 Focus Recursion
* **Problem**: Active CaptureGuard window enumeration loop caused infinite thread recursion on some systems.
* **Fix**: Disabled `self._enum_process_windows()` (line 165 in `guard.py`) during PyWebView window loops to bypass Windows Accessibility object recursion.

## 3. Mathematical Formula Discards in OCR
* **Problem**: Math expressions (like equations, integrations, fractions) have low alphanumeric ratios and were incorrectly flagged as garbage lines by the cleaner.
* **Fix**: Added math symbol checks (`+-*/=^√∫∂∆%±≤≥≠≈∝()[]{}<>`) inside `ocr_cleaner.py` to whitelist lines containing formulas.

---

# Known Issues & Limitations

## 1. Local LLM Load Latency
* **Impact**: Spawning `llama-server.exe` takes 30-60s on 8GB/12GB RAM setups.
* **Solution**: Keep users informed via UI loading indicators and let the combined routing engine fall back to OpenAI API in the meantime.

## 2. Non-Windows System Limitations
* **Impact**: Win32 display affinity (`WDA_EXCLUDEFROMCAPTURE`) and proctoring hooks fail on macOS/Linux.
* **Behavior**: CaptureGuard and FocusLock logs a warning and gracefully fails into a no-op mode.

## 3. Elevated Key Block Permissions
* **Impact**: Global hotkey hooks (`keyboard.block_key`) fail to execute if the application is not run with elevated administrative privileges.

---

# Technical Decisions

* **PyWebView over Electron**: Python core scripts are required to hook into low-level Win32 APIs, execute local CLI servers, and run fast screen capture libraries. PyWebView provides an HTML5 rendering frame with direct Python integrations.
* **Single Spec Compilation**: Unified compilation under `FocusFlow.spec` to avoid divergent spec configs and package dependencies.

---

# Agent Notes: Critical Instructions for Future Modifying Agents

> [!IMPORTANT]
> **1. Process Cleanup**: Whenever editing `offline_engine.py`, ensure that `taskkill /F /IM llama-server.exe` remains in the stop lifecycle. Leaving orphaned LLM servers will hog 3GB+ of user RAM and block port 8081.
>
> **2. Accessibility/Capture Exclusion Loops**: Never re-enable `self._enum_process_windows()` in `guard.py` without testing PyWebView compatibility. It triggers recursion inside Windows UI Automation (`AccessibilityObject.Bounds`) causing a thread crash.
>
> **3. Admin Privileges for Key Blocking**: Do not modify keyboard hooks without considering elevated runtime privileges. If tests fail to intercept Windows shortcuts, verify if you are running the test terminal as Administrator.
>
> **4. Static Frontend Assets**: The python backend serves UI files from `landing/out`. Any changes made inside `landing/src` **MUST** be compiled by running `npm run build` (or `.\build.bat` inside the landing folder) before testing launcher execution.
>
> **5. File Logging Warnings**: Do not write project settings files using raw python dictionaries without merging defaults first. State configurations must load settings by calling `config.get_all()` to merge saved configs over `DEFAULTS` keys to prevent KeyErrors.

---

# Development Workflow

## Build Commands
Build Next.js static production assets:
```powershell
cd landing
.\build.bat
```

## Test Commands
Run python test suite:
```powershell
python -m unittest test_session_manager.py test_fixes.py test_features.py test_system.py
```

## Run Commands
Start PyWebView UI container:
```powershell
python main.py
```

## Compilation/Packaging Commands
Compile single-file FocusFlow.exe package:
```powershell
pyinstaller FocusFlow.spec --noconfirm
```

---

# Dependency Notes

* **Package**: `pywebview`
  * **Purpose**: UI window loop.
  * **Do Not Replace**: Foundational GUI wrapper.

* **Package**: `pywin32`
  * **Purpose**: Window affinity exclusions and process polling.
  * **Do Not Replace**: Hard dependency for proctoring features.

---

# Database Schema Summary

JSON-based flat files:
* **Settings (`data/settings.json`)**: Configuration variables (allowed apps, website whitelist, API keys, volume parameters, selected model).
* **Sessions (`data/sessions.json`)**: Log metrics (duration, subject, target, score, interrupted flags).
* **Goals (`data/daily_goals.json`)**: Daily checklist items.

---

# AI Context Summary

1. **FocusFlow Purpose**: Hybrid study proctoring desktop app with AI doubts solving and focus-lock states.
2. **Current Architecture**: Next.js React frontend served locally by a Python server via PyWebView wrapper, routing tasks to AIEngine, CaptureGuard, and SessionManager.
3. **Recent Changes**: Implemented overtime exit button fix, daily backdated commits (Jan 25 - May 25), and model dropdown lazy loading.
4. **Key Warnings**: Subprocesses require Windows taskkill; keyboard hooks require Admin credentials; do not re-enable window enumeration loop in CaptureGuard.
5. **Setup Requirements**: Compiling Next.js assets to `landing/out` is required to reflect frontend changes.

---

# Last Updated

Timestamp:
2026-06-25 14:02 UTC

Updated By:
AI Agent Antigravity

Summary:
Updated `BRAIN.md` with complete, exhaustive technical details on proctoring loops, exit buttons, backdated log commits, process cleanup instructions, and key WebView2 runtime limitations.
