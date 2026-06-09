"""
FocusFlow — Offline-Only Entry Point
====================================
Launches FocusFlow locked to Offline Mode.
"""

from main import FocusFlowApp

if __name__ == "__main__":
    app = FocusFlowApp(run_mode="offline")
    app.root.mainloop()
