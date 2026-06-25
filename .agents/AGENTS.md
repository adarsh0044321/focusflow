# FocusFlow AI Agent Rules

This workspace enforces strict guidelines for documentation integrity and synchronization. All agents operating on this codebase must adhere to the following rules:

## Rules

### 1. Maintain Documentation Integrity
You must continuously update and maintain the local documentation files after every response, execution cycle, or modification you make. This includes:
*   **BRAIN.md**: Permanent codebase structure and technical warnings.
*   **ROADMAP.md**: Future release targets and backlog entries.
*   **DECISIONS.md**: Architectural records and structural choices.
*   **HANDOVER.md**: Current task status and direct handover notes for the next agent.
*   **SESSION.md**: Active scratchpad notes for your current development session.

### 2. Strict Git Evasion Constraint
Do not commit or push any of the following files to remote Git repositories under any circumstances:
*   `BRAIN.md`
*   `ROADMAP.md`
*   `DECISIONS.md`
*   `HANDOVER.md`
*   `SESSION.md`

These files are configured in `.gitignore` and must remain local-only forever.
