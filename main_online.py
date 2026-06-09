"""
FocusFlow — Online-Only Entry Point
===================================
Launches FocusFlow locked to Online Mode.
"""

from main import FocusFlowApp

if __name__ == "__main__":
    app = FocusFlowApp(run_mode="online")
    app.root.mainloop()
