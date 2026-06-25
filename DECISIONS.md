# DECISIONS.md

Purpose: Stores architecture and engineering decisions.

---

# Decision Template

## ADR-000: Title

Date:
YYYY-MM-DD

Status:
Accepted / Rejected / Superseded

---

### Problem

What problem needed solving?

---

### Options Considered

#### Option A

Pros:
* Item

Cons:
* Item

---

#### Option B

Pros:
* Item

Cons:
* Item

---

### Decision

Chosen approach.

---

### Reasoning

Why it was chosen.

---

### Consequences

Positive:
* Item

Negative:
* Item

---

### Related Files

* path/to/file

---

# Decision History

## ADR-001: Choose PyWebView over Electron / Tauri

Date:
2026-06-14

Status:
Accepted

### Problem
The application requires direct system access to Win32 APIs for screen capture exclusions (`SetWindowDisplayAffinity`), global keyboard hooking (`keyboard.block_key`), and Precision Touchpad registry locks. Renders need to execute with minimal inter-process communication latency and a light package footprint.

### Options Considered

#### Electron or Tauri
Pros:
* Broad ecosystem, polished window frame capabilities, and robust packaging pipelines.

Cons:
* Spawning Node/Rust sidecars for Python operations adds IPC latency, complicates double-bundling, and increases the final executable size.

#### PyWebView
Pros:
* Allows writing both the core Win32 systems logic and UI bridging scripts in native Python.
* Uses the built-in system Webview2 control, resulting in a significantly smaller binary size.
* Fast direct python-to-JS object bridging.

Cons:
* Frameless window scaling on Windows High-DPI screens requires manual ctypes calculations.

### Decision
Chosen **PyWebView** as the UI container framework.

### Reasoning
Writing both the core application and the proctoring lock states in Python avoids multi-language packaging bottlenecks, yields a lighter executable, and lets us bridge JavaScript calls straight to the core modules without IPC message serialization.

### Consequences
Positive:
* Packaged single executable is under 80MB (Lite release).
* Low latency bridged calls for screen capture, OCR, and AI queries.

Negative:
* High-DPI scaling and window coordinates offset had to be manually calculated using ctypes scaling metrics.

### Related Files
* [main.py](file:///c:/Users/JAISINGH/.gemini/antigravity/scratch/studytool/main.py)
* [app_bridge.py](file:///c:/Users/JAISINGH/.gemini/antigravity/scratch/studytool/app_bridge.py)
* [FocusFlow.spec](file:///c:/Users/JAISINGH/.gemini/antigravity/scratch/studytool/FocusFlow.spec)

---

## ADR-002: Bypassing Window Process Enumeration in Capture Guard

Date:
2026-06-15

Status:
Accepted

### Problem
In Windows environment loops, calling `EnumWindows` inside `guard.py` to identify and protect all windows belonging to the FocusFlow PID triggered thread recursion inside Microsoft WebView2's Accessibility UI Automation trees (`AccessibilityObject.Bounds`), causing the application thread to crash.

### Options Considered

#### Full Process Window Enumeration (EnumWindows)
Pros:
* Automatically protects every child window, dialog, and dropdown that is spawned.

Cons:
* Triggers an infinite loop UI Automation recursion crash.

#### Viewport Handle Protection
Pros:
* Zero loop crash risk since it targets the exact main viewport window handle.

Cons:
* Requires manually registering dialog handles (like Tkinter overlays) as they are created.

### Decision
Only apply display affinity exclusions directly to the main PyWebView viewport HWND and active Tkinter popups. Comment out `self._enum_process_windows()` in [guard.py](file:///c:/Users/JAISINGH/.gemini/antigravity/scratch/studytool/guard.py).

### Reasoning
Preventing crashes inside the WebView2 window viewport takes precedence. Viewport handle protection covers 100% of the study screen, and individual handles can be protected explicitly if necessary.

### Consequences
Positive:
* Application is completely stable under WebView2 loops with zero crashes.

Negative:
* Requires explicit calls to protect new windows (e.g. Tkinter overlays) using `protect_all_tk_windows(root)`.

### Related Files
* [guard.py](file:///c:/Users/JAISINGH/.gemini/antigravity/scratch/studytool/guard.py)
* [main.py](file:///c:/Users/JAISINGH/.gemini/antigravity/scratch/studytool/main.py)

---

## ADR-003: Overtime Exit Button Hold-Requirement Bypass

Date:
2026-06-17

Status:
Accepted

### Problem
In Moderate, Strict, and Very Strict focus sessions, students are required to click and hold the exit button for 10 seconds to log out. However, if the target session duration is completed, requiring a 10-second emergency hold is frustrating and redundant.

### Decision
Condition the exit button behavior on the session countdown timer:
* If `timeLeft > 0`, display the "Hold Click to Emergency Exit (10s)" red button (which penalizes the study score on interrupt).
* If `timeLeft <= 0`, swap to an immediate green "Finish Session & Log Stats" button.

### Consequences
Positive:
* Streamlined completion workflow for completed study sessions.
* Retains proctoring penalties during active focus intervals.

### Related Files
* [landing/src/app/dashboard/page.tsx](file:///c:/Users/JAISINGH/.gemini/antigravity/scratch/studytool/landing/src/app/dashboard/page.tsx)
