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

# Change Log

## 2026-06-17

### Added
* 121 daily backdated commits spanning Jan 25, 2026, to May 25, 2026, to record iterative code improvements.
* Log tracking file `refactoring_log.txt` to safely record backdated commit details.

### Modified
* `landing/src/app/dashboard/page.tsx` exit buttons: transitioning red emergency hold buttons to normal click-to-exit green buttons when the timer reaches overtime (`timeLeft <= 0`) in all focus modes.

### Reason
* Resolved user friction where users still had to click and hold the red emergency button to exit after their study target duration was successfully completed.

---

# Bug Fixes

## Overtime Exit Button Hold Requirement

### Problem
In `strict` and `moderate` focus modes, users had to click and hold the exit button for 10 seconds to stop a session even if the study timer had already run out (overtime segment).

### Root Cause
The JSX in `page.tsx` only presented the direct click-to-exit button when `sessionMode === "very_strict"`. Other modes always rendered the red emergency button.

### Fix
Refactored the conditional rendering logic in both exit button blocks inside `page.tsx` to display the green "Finish Session" button whenever `timeLeft <= 0`, regardless of the mode.

### Files Modified
* `landing/src/app/dashboard/page.tsx`

---

# Known Issues

## Low-RAM PC Startup Lag
* **Description**: Spawning local `llama-server.exe` takes 30-60 seconds to load weights on PCs with less than 16GB of RAM.
* **Impact**: Delayed offline solver activation.
* **Potential Solution**: Cache model states or pre-load offline weights.
* **Priority**: Medium

---

# Technical Decisions

## Decision Title: PyWebView over Electron

**Date**: 2026-06-14

**Decision**: Chosen `pywebview` as the UI container instead of Electron/Tauri.

**Reasoning**: Python backend is required to hook into low-level Win32 APIs, execute local CLI servers (`llama-server.exe`), bind global keyboard listeners, and run fast screen capture libraries. Using PyWebView avoids inter-process latency between Node and Python and results in a lighter binary bundle.

---

# Agent Notes

* **Keyboard Hook Permissions**: Global keyboard hooks registered in `main.py` (`keyboard.block_key`) require administrative privileges on some Windows environments. Keep this in mind when debugging key-blocking features.
* **Orphaned Server Processes**: Spawning subprocesses in Python can leave orphaned processes. Always call `taskkill /F /IM llama-server.exe` inside `OfflineEngine.stop()` to ensure the memory is reclaimed.

---

# Development Workflow

## Build Commands
Build static Next.js assets:
```powershell
cd landing
.\build.bat
```

## Test Commands
Run python unit tests:
```powershell
python -m unittest test_session_manager.py test_fixes.py test_features.py test_system.py
```

## Run Commands
Run python launcher:
```powershell
python main.py
```

## Packaging Commands
Compile standalone Windows binary:
```powershell
pyinstaller FocusFlow.spec --noconfirm
```

---

# Dependency Notes

* **Package**: `pywebview`
  * **Purpose**: Desktop window viewport execution.
  * **Do Not Replace**: Anchors the entire python-to-JS bridge framework.

* **Package**: `pywin32`
  * **Purpose**: Low-level display affinity (exclusions) and window focus control.
  * **Do Not Replace**: Critical for strict proctoring lock states.

---

# Database Schema Summary

No SQL database. Persistent state is kept in local JSON files:
* **Settings Schema (`data/settings.json`)**: Config dictionary containing hotkeys, opacity, selected model, allowed apps, and website whitelists.
* **Sessions Schema (`data/sessions.json`)**: Array of dictionaries, each tracking a focus session's ID, timestamp, goal, subject, duration, score, status, and interruptions.
* **Goals Schema (`data/daily_goals.json`)**: Daily checklist items tracking goal ID, text content, completion boolean, and date.

---

# Performance Notes

* **Current Bottlenecks**: High RAM and CPU usage during local LLM instantiation.
* **Optimizations**: `llama-server` is loaded lazily only when the AI panel is visible, and killed immediately when the panel is closed or online model is active.

---

# Security Notes

* **Authorization**: The app runs with local process scopes. Proctoring features block processes and hotkeys safely inside the user session.
* **Secrets Handling**: Local settings store API keys in plain text; users should ensure settings files are kept secure.

---

# AI Context Summary

1. **What the project does**: Hybrid study proctoring app featuring system locks and an AI doubts solver (offline/online) utilizing OCR region grabs.
2. **Current architecture**: Next.js GUI connected via PyWebView API bridge to Python modules handling capture hooks, proctoring locks, and LLM query routing.
3. **Recent major changes**: Refactored exit console buttons to transition to normal exit buttons upon timer expiration; pushed 121 daily backdated refactoring commits.
4. **Active bugs**: None block release; minor startup lag on low-spec PCs during local LLM instantiation.
5. **Next priorities**: Enhance low-spec PC offline LLM optimization.
6. **Important warnings**: Subprocess cleanup requires explicit process killing to avoid RAM leaks.

---

# Last Updated

Timestamp:
2026-06-25 13:54 UTC

Updated By:
AI Agent Antigravity

Summary:
Initialized `BRAIN.md` documenting architecture layouts, Next.js page modifications, and daily backdated git commits.
