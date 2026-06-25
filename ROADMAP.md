# ROADMAP.md

Purpose: Defines the future direction of the project.

---

# Vision

Create the ultimate premium, secure, and distractions-locked hybrid study dashboard. By combining local and cloud AI assistance with low-level Windows proctoring, FocusFlow protects students from distractions during high-stakes preparation (e.g., JEE, UPSC) while providing instantDoubts Solver utilities.

---

# Current Milestone

Milestone:
v1.3.0

Goal:
Unified AI Engine options, lazy server subprocess instantiation, and overtime exit button hold-free triggers.

Status:
Completed

Completion:
100%

---

# Upcoming Milestones

## Milestone: v1.4.0

Target Date:
2026-07-20

Objectives:
* **Low-Spec Offline LLM Optimization**: Implement GGUF model quantization configuration parameters inside the settings tab to support 4GB/6GB RAM devices.
* **Dynamic Context Swapping**: Dynamically adjust Phi-3 context sizes based on the user's available physical RAM to prevent system paging lag.
* **Cross-Platform Proctoring Stubs**: Stub keyboard blocking and display capture exclusion handlers gracefully on macOS and Linux, enabling visual dry-runs for development.

Success Criteria:
* The offline model server launches and becomes ready in under 15 seconds on a machine with 8GB RAM.
* The source builds successfully on macOS/Linux with zero third-party library faults (gracefully logging warnings).

Risks:
* Deep system API integrations for screen capture affinity are highly OS-specific and might require platform-specific sidecar builds.
* Extreme RAM constraints on target low-spec devices may crash llama-server subprocesses unexpectedly.

---

## Milestone: v1.5.0

Objectives:
* **Encrypted Cloud Sync**: Integrate a secure backend endpoint to backup local metrics (`sessions.json` and `daily_goals.json`).
* **Peer Study Heatmaps**: Allow students to optionally share consistency heatmap stats charts with peer study groups.

Dependencies:
* Secure cloud database API endpoints.
* Authenticated user session managers.

---

# Feature Backlog

## High Priority

### Dynamic CPU Thread Allocation
Description:
Automatically adjust llama-server thread allocations based on real-time CPU core utilization to prevent GUI stuttering.

Expected Impact:
High

Estimated Complexity:
Medium

Dependencies:
`psutil` system metrics integration.

---

## Medium Priority

### OCR Translation Mode
Description:
Introduce language translation options for scanned physics/chemistry mathematical and scientific formulas.

Expected Impact:
Medium

Estimated Complexity:
Medium

Dependencies:
Enhanced prompt templates and cleaning regex.

---

## Low Priority

### Custom HUD Themes
Description:
Provide additional UI theme palettes (such as Lofi Workspace, Cyberpunk Dark, or Sleek Glass-Light mode).

Expected Impact:
Low

Estimated Complexity:
Low

Dependencies:
Next.js tailwind theme classes.

---

# Technical Debt

## Global Configuration Persistence
Description:
Settings, history logs, and goals databases are fetched synchronously from multiple flat JSON files on disk.

Reason:
Bootstrapped during early prototyping for simplicity.

Impact:
Performance / Maintainability

Priority:
Medium

---

# Research Items

## Deep Win32 Hook Hooking
Questions:
* Can we prevent Ctrl+Alt+Del access natively in Python without registering kernel-level driver hooks?
* How does display affinity behave on multi-GPU setups?

Potential Approaches:
* Researching Windows Credential Provider interfaces.
* Testing display affinity APIs on hybrid laptop graphics configurations (Intel + Nvidia/AMD).

---

# Stretch Goals

* Ambient audio track library expansion (lofi beats streaming).
* Integration with physical desktop pomodoro hardware.

---

# Recently Completed

## 2026-06-25
Completed:
* Consolidating separate LLM toggle buttons into a single AI dropdown selector.
* Implementing lazy startup/shutdown of local `llama-server.exe` to save PC resources.
* Overtime exit button hold-free click controls when the session timer reaches `timeLeft <= 0`.
* Exhaustive verification of proctoring locks, touchpad registry backups, and PyInstaller package scripts.

Notes:
Lazy subprocess loading significantly improved user PC responsiveness and prevented orphaned servers on crash exits.
